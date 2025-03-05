from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
import json
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import *
import razorpay
from django.conf import settings
from django.utils import timezone


def index(request):
    # Always order posts by date (most recent first)
    all_posts = Post.objects.all().order_by('-date_created')
    
    paginator = Paginator(all_posts, 400)
    page_number = request.GET.get('page') or 1
    posts = paginator.get_page(page_number)
    
    followings = []
    suggestions = []
    if request.user.is_authenticated:
        followings = Follower.objects.filter(followers=request.user).values_list('user', flat=True)
        # Order suggestions by username (or any other fixed order)
        suggestions = User.objects.exclude(pk__in=followings)\
                                  .exclude(username=request.user.username)\
                                  .order_by('username')[:6]
    
    return render(request, "network/index.html", {
        "posts": posts,
        "suggestions": suggestions,
        "page": "all_posts",
        "profile": False
    })



def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        fname = request.POST["firstname"]
        lname = request.POST["lastname"]
        profile = request.FILES.get("profile")
        cover = request.FILES.get("cover")
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })
        try:
            user = User.objects.create_user(username, email, password)
            user.first_name = fname
            user.last_name = lname
            user.profile_pic = profile if profile else "profile_pic/no_pic.png"
            user.cover = cover
            user.save()
            Follower.objects.create(user=user)
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")


def profile(request, username):
    user = User.objects.get(username=username)
    all_posts = Post.objects.filter(creater=user).order_by('-date_created')
    paginator = Paginator(all_posts, 299)  # 10 posts per page
    page_number = request.GET.get('page') or 1
    posts = paginator.get_page(page_number)
    followings = []
    suggestions = []
    follower = False
    if request.user.is_authenticated:
        followings = Follower.objects.filter(followers=request.user).values_list('user', flat=True)
        suggestions = User.objects.exclude(pk__in=followings).exclude(username=request.user.username).order_by("?")[:6]
        if request.user in Follower.objects.get(user=user).followers.all():
            follower = True
    follower_count = Follower.objects.get(user=user).followers.all().count()
    following_count = Follower.objects.filter(followers=user).count()
    return render(request, 'network/profile.html', {
        "username": user,
        "posts": posts,
        "posts_count": all_posts.count(),
        "suggestions": suggestions,
        "page": "profile",
        "is_follower": follower,
        "follower_count": follower_count,
        "following_count": following_count
    })


def following(request):
    if request.user.is_authenticated:
        following_user = Follower.objects.filter(followers=request.user).values('user')
        all_posts = Post.objects.filter(creater__in=following_user).order_by('-date_created')
        paginator = Paginator(all_posts, 10)
        page_number = request.GET.get('page') or 1
        posts = paginator.get_page(page_number)
        followings = Follower.objects.filter(followers=request.user).values_list('user', flat=True)
        suggestions = User.objects.exclude(pk__in=followings).exclude(username=request.user.username).order_by("?")[:6]
        return render(request, "network/index.html", {
            "posts": posts,
            "suggestions": suggestions,
            "page": "following"
        })
    else:
        return HttpResponseRedirect(reverse('login'))


def saved(request):
    if request.user.is_authenticated:
        all_posts = Post.objects.filter(savers=request.user).order_by('-date_created')
        paginator = Paginator(all_posts, 10)
        page_number = request.GET.get('page') or 1
        posts = paginator.get_page(page_number)
        followings = Follower.objects.filter(followers=request.user).values_list('user', flat=True)
        suggestions = User.objects.exclude(pk__in=followings).exclude(username=request.user.username).order_by("?")[:6]
        return render(request, "network/index.html", {
            "posts": posts,
            "suggestions": suggestions,
            "page": "saved"
        })
    else:
        return HttpResponseRedirect(reverse('login'))


@login_required
def create_post(request):
    if request.method == 'POST':
        text = request.POST.get('text')
        pic = request.FILES.get('picture')
        try:
            Post.objects.create(creater=request.user, content_text=text, content_image=pic)
            return HttpResponseRedirect(reverse('index'))
        except Exception as e:
            return HttpResponse(f"Error creating post: {e}")
    else:
        return render(request, "network/create_post.html")


@csrf_exempt
def like_post(request, id):
    if request.user.is_authenticated:
        if request.method == 'PUT':
            post = Post.objects.get(pk=id)
            try:
                post.likers.add(request.user)
                post.save()
                return HttpResponse(status=204)
            except Exception as e:
                return HttpResponse(e)
        else:
            return HttpResponse("Method must be 'PUT'")
    else:
        return HttpResponseRedirect(reverse('login'))


@csrf_exempt
def unlike_post(request, id):
    if request.user.is_authenticated:
        if request.method == 'PUT':
            post = Post.objects.get(pk=id)
            try:
                post.likers.remove(request.user)
                post.save()
                return HttpResponse(status=204)
            except Exception as e:
                return HttpResponse(e)
        else:
            return HttpResponse("Method must be 'PUT'")
    else:
        return HttpResponseRedirect(reverse('login'))


@csrf_exempt
def save_post(request, id):
    if request.user.is_authenticated:
        if request.method == 'PUT':
            post = Post.objects.get(pk=id)
            try:
                post.savers.add(request.user)
                post.save()
                return HttpResponse(status=204)
            except Exception as e:
                return HttpResponse(e)
        else:
            return HttpResponse("Method must be 'PUT'")
    else:
        return HttpResponseRedirect(reverse('login'))

@login_required
def edit_profile(request):
    user = request.user
    if request.method == "POST":
        # Update fields if provided
        user.first_name = request.POST.get("first_name", user.first_name)
        user.last_name = request.POST.get("last_name", user.last_name)
        user.bio = request.POST.get("bio", user.bio)
        if request.FILES.get("profile_pic"):
            user.profile_pic = request.FILES.get("profile_pic")
        if request.FILES.get("cover"):
            user.cover = request.FILES.get("cover")
        user.save()
        return redirect("profile", username=user.username)
    return render(request, "network/edit_profile.html", {"user": user})

@csrf_exempt
def unsave_post(request, id):
    if request.user.is_authenticated:
        if request.method == 'PUT':
            post = Post.objects.get(pk=id)
            try:
                post.savers.remove(request.user)
                post.save()
                return HttpResponse(status=204)
            except Exception as e:
                return HttpResponse(e)
        else:
            return HttpResponse("Method must be 'PUT'")
    else:
        return HttpResponseRedirect(reverse('login'))


@csrf_exempt
def follow(request, username):
    if request.user.is_authenticated:
        if request.method == 'PUT':
            user = User.objects.get(username=username)
            try:
                follower, created = Follower.objects.get_or_create(user=user)
                follower.followers.add(request.user)
                follower.save()
                return JsonResponse({'status': 'followed'}, status=200)  # Return JSON response
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=400)
        else:
            return JsonResponse({'error': "Method must be 'PUT'"}, status=405)
    else:
        return JsonResponse({'error': 'Unauthorized'}, status=401)


@csrf_exempt
def unfollow(request, username):
    if request.user.is_authenticated:
        if request.method == 'PUT':
            user = User.objects.get(username=username)
            try:
                follower = Follower.objects.get(user=user)
                follower.followers.remove(request.user)
                follower.save()
                return JsonResponse({'status': 'unfollowed'}, status=200)  # Return JSON response
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=400)
        else:
            return JsonResponse({'error': "Method must be 'PUT'"}, status=405)
    else:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

@login_required
def toggle_follow(request, username):
    user_to_follow = get_object_or_404(User, username=username)
    follower, created = Follower.objects.get_or_create(user=user_to_follow)

    if request.user in follower.followers.all():
        follower.followers.remove(request.user)
    else:
        follower.followers.add(request.user)

    follower.save()
    return redirect('profile', username=username)

@login_required
@csrf_exempt
def comment(request, post_id):
    if request.user.is_authenticated:
        if request.method == 'POST':
            data = json.loads(request.body)
            comment_text = data.get('comment_text')
            post = Post.objects.get(id=post_id)
            try:
                newcomment = Comment.objects.create(post=post, commenter=request.user, comment_content=comment_text)
                post.comment_count += 1
                post.save()
                return JsonResponse([newcomment.serialize()], safe=False, status=201)
            except Exception as e:
                return HttpResponse(e)
        post = Post.objects.get(id=post_id)
        comments = Comment.objects.filter(post=post).order_by('-comment_time').all()
        return JsonResponse([comment.serialize() for comment in comments], safe=False)
    else:
        return HttpResponseRedirect(reverse('login'))

def write_comment_view(request, post_id):
    if request.method == 'POST' and request.user.is_authenticated:
        post = get_object_or_404(Post, id=post_id)
        comment_text = request.POST.get('comment', '').strip()
        if comment_text:
            Comment.objects.create(post=post, commenter=request.user, comment_content=comment_text)
            post.comment_count += 1
            post.save()
    return redirect(request.META.get('HTTP_REFERER', 'index'))


@login_required
def toggle_like(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        if request.user in post.likers.all():
            post.likers.remove(request.user)
        else:
            post.likers.add(request.user)
        post.save()
        # Get the referring URL (or default to index)
        referrer = request.META.get('HTTP_REFERER', reverse("index"))
        # Remove any existing fragment if present
        if '#' in referrer:
            referrer = referrer.split('#')[0]
        # Append the fragment to jump to the same post
        return redirect(referrer + "#post-" + str(post_id))
    else:
        return HttpResponse("Method not allowed", status=405)

@csrf_exempt
def delete_post(request, post_id):
    if request.user.is_authenticated:
        if request.method == 'POST':  # Change from 'PUT' to 'POST'
            post = Post.objects.get(id=post_id)
            if request.user == post.creater:
                try:
                    post.delete()
                    return HttpResponseRedirect(reverse('index'))  # Redirect after deletion
                except Exception as e:
                    return HttpResponse(e)
            else:
                return HttpResponse(status=404)
        else:
            return HttpResponse("Method must be 'POST'")
    else:
        return HttpResponseRedirect(reverse('login'))


def search_users(request):
    query = request.GET.get('query', '')
    users = User.objects.filter(username__icontains=query) if query else []
    
    # Add suggestions
    suggestions = []
    if request.user.is_authenticated:
        followings = Follower.objects.filter(followers=request.user).values_list('user', flat=True)
        suggestions = User.objects.exclude(pk__in=followings)\
                                .exclude(username=request.user.username)\
                                .order_by('-is_premium', '?')[:6]
    
    return render(request, 'network/search_results.html', {
        'users': users, 
        'query': query,
        'suggestions': suggestions,
        'page': 'search'
    })

@login_required
def edit_profile(request):
    user = request.user
    # Add suggestions
    followings = Follower.objects.filter(followers=request.user).values_list('user', flat=True)
    suggestions = User.objects.exclude(pk__in=followings)\
                            .exclude(username=request.user.username)\
                            .order_by('-is_premium', '?')[:6]
    
    if request.method == "POST":
        # Update fields if provided
        user.first_name = request.POST.get("first_name", user.first_name)
        user.last_name = request.POST.get("last_name", user.last_name)
        user.bio = request.POST.get("bio", user.bio)
        if request.FILES.get("profile_pic"):
            user.profile_pic = request.FILES.get("profile_pic")
        if request.FILES.get("cover"):
            user.cover = request.FILES.get("cover")
        user.save()
        return redirect("profile", username=user.username)
    return render(request, "network/edit_profile.html", {
        "user": user,
        "suggestions": suggestions,
        "page": "edit_profile"
    })

@login_required
def premium_subscription(request):
    # Initialize Razorpay client
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    
    # Create order on page load, not just on POST
    payment = client.order.create({
        'amount': settings.PREMIUM_PRICE,
        'currency': settings.RAZORPAY_CURRENCY,
        'payment_capture': '1'
    })
    
    # Add suggestions
    followings = Follower.objects.filter(followers=request.user).values_list('user', flat=True)
    suggestions = User.objects.exclude(pk__in=followings)\
                            .exclude(username=request.user.username)\
                            .order_by('-is_premium', '?')[:6]
    
    context = {
        'suggestions': suggestions,
        'page': 'premium',
        'payment': payment,
        'key_id': settings.RAZORPAY_KEY_ID
    }
    
    return render(request, "network/premium.html", context)

@login_required
@csrf_exempt
def premium_success(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            
            # Verify the payment signature
            params_dict = {
                'razorpay_payment_id': data.get('razorpay_payment_id'),
                'razorpay_order_id': data.get('razorpay_order_id'),
                'razorpay_signature': data.get('razorpay_signature')
            }
            
            # Verify signature
            client.utility.verify_payment_signature(params_dict)
            
            # Update user status
            request.user.is_premium = True
            request.user.premium_since = timezone.now()
            request.user.save()
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})