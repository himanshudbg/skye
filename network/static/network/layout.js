// JavaScript for like/unlike, comment, and save functionality

document.addEventListener("DOMContentLoaded", () => {
  // Initialization code if needed
});

// Toggle like/unlike
function toggleLike(el, event) {
  event.preventDefault();
  const postId = el.dataset.post_id;
  const isLiked = el.dataset.liked === "true";
  const url = `/n/post/${postId}/${isLiked ? 'unlike' : 'like'}`;

  fetch(url, { method: 'PUT' })
    .then(response => {
      if (response.ok) {
        const countElem = el.querySelector('.likes_count');
        const count = parseInt(countElem.innerText, 10);
        countElem.innerText = isLiked ? count - 1 : count + 1;
        el.querySelector('.svg-span').innerHTML = `<span class="material-icons text-2xl">${isLiked ? 'favorite_border' : 'favorite'}</span>`;
        el.dataset.liked = !isLiked;
      } else {
        console.error("Error toggling like");
      }
    })
    .catch(console.error);
}

// Toggle comment section
function toggleComment(el, event) {
  event.preventDefault();
  const postId = el.dataset.post_id;
  const commentDiv = document.getElementById(`comment-div-${postId}`);
  const commentIcon = document.getElementById(`comment-icon-${postId}`);

  commentDiv.classList.toggle("hidden");
  commentIcon.innerText = commentDiv.classList.contains("hidden") ? "chat_bubble_outline" : "chat_bubble";
}

// Toggle save/unsave
function toggleSave(el, event) {
  event.preventDefault();
  const postId = el.dataset.post_id;
  const isSaved = el.dataset.saved === "true";
  const url = `/n/post/${postId}/${isSaved ? 'unsave' : 'save'}`;

  fetch(url, { method: 'PUT' })
    .then(response => {
      if (response.ok) {
        el.querySelector('.svg-span').innerHTML = `<span class="material-icons text-2xl">${isSaved ? 'bookmark_border' : 'bookmark'}</span>`;
        el.dataset.saved = !isSaved;
      } else {
        console.error("Error toggling save");
      }
    })
    .catch(console.error);
}

// Get CSRF token from cookies
function getCookie(name) {
  const cookies = document.cookie.split(";");
  for (let cookie of cookies) {
    cookie = cookie.trim();
    if (cookie.startsWith(`${name}=`)) {
      return decodeURIComponent(cookie.substring(name.length + 1));
    }
  }
  return null;
}

// Redirect functions
function goto_register() {
  window.location.href = "/n/register";
}

function goto_login() {
  window.location.href = "/n/login";
}

function followUser(el, username) {
  const url = `/${username}/follow`;
  fetch(url, {
    method: 'PUT',
    headers: {
      'X-CSRFToken': getCookie('csrftoken'), // Ensure CSRF token is included
      'Content-Type': 'application/json'
    },
  })
  .then(response => response.json())
  .then(data => {
    if (data.status === 'followed') {
      el.innerText = 'Followed'; // Update button text to "Followed"
      el.classList.add('bg-gray-500'); // Change button style
      el.classList.remove('bg-blue-600', 'hover:bg-blue-700');
      el.disabled = true; // Disable button after following
    } else {
      console.error('Failed to follow user:', data.error);
    }
  })
  .catch(error => console.error('Error:', error));
}

function unfollowUser(el, username, page) {
  const url = `/${username}/unfollow`;
  fetch(url, {
    method: 'PUT',
    headers: {
      'X-CSRFToken': getCookie('csrftoken'), // Ensure CSRF token is included
      'Content-Type': 'application/json'
    },
  })
  .then(response => response.json())
  .then(data => {
    if (data.status === 'unfollowed') {
      location.reload(); // Refresh the page
    } else {
      console.error('Failed to unfollow user:', data.error);
    }
  })
  .catch(error => console.error('Error:', error));
}