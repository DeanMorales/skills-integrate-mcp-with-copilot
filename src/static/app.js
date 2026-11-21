document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const signupContainer = document.getElementById("signup-container");
  const messageDiv = document.getElementById("message");
  const loginButton = document.getElementById("login-button");
  const logoutButton = document.getElementById("logout-button");
  const loginDialog = document.getElementById("login-dialog");
  const loginForm = document.getElementById("login-form");
  const loginMessage = document.getElementById("login-message");
  const cancelLoginButton = document.getElementById("cancel-login");
  let teacherCredentials = null;

  function showMessage(message, type) {
    messageDiv.textContent = message;
    messageDiv.className = type;
    messageDiv.classList.remove("hidden");
    setTimeout(() => messageDiv.classList.add("hidden"), 5000);
  }

  function showLoginError(message) {
    loginMessage.textContent = message;
    loginMessage.className = "error";
  }

  function authorizationHeader(credentials) {
    const bytes = new TextEncoder().encode(
      `${credentials.username}:${credentials.password}`
    );
    const binary = Array.from(bytes, (byte) => String.fromCharCode(byte)).join("");
    return `Basic ${btoa(binary)}`;
  }

  function updateAuthControls() {
    loginButton.classList.toggle("hidden", Boolean(teacherCredentials));
    logoutButton.classList.toggle("hidden", !teacherCredentials);
    signupContainer.classList.toggle("hidden", !teacherCredentials);
  }

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";
      while (activitySelect.options.length > 1) {
        activitySelect.remove(1);
      }

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft =
          details.max_participants - details.participants.length;

        // Create participants HTML with delete icons instead of bullet points
        const participantsHTML =
          details.participants.length > 0
            ? `<div class="participants-section">
              <h5>Participants:</h5>
              <ul class="participants-list">
                ${details.participants
                  .map(
                    (email) => `<li>
                      <span class="participant-email">${email}</span>
                      ${
                        teacherCredentials
                          ? `<button class="delete-btn" data-activity="${name}" data-email="${email}" aria-label="Remove ${email} from ${name}">Remove</button>`
                          : ""
                      }
                    </li>`
                  )
                  .join("")}
              </ul>
            </div>`
            : `<p><em>No participants yet</em></p>`;

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-container">
            ${participantsHTML}
          </div>
        `;

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });

      // Add event listeners to delete buttons
      activitiesList.querySelectorAll(".delete-btn").forEach((button) => {
        button.addEventListener("click", handleUnregister);
      });
    } catch (error) {
      activitiesList.innerHTML =
        "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle unregister functionality
  async function handleUnregister(event) {
    const button = event.target;
    const activity = button.getAttribute("data-activity");
    const email = button.getAttribute("data-email");

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/unregister?email=${encodeURIComponent(email)}`,
        {
          method: "DELETE",
          headers: {
            Authorization: authorizationHeader(teacherCredentials),
          },
        }
      );

      const result = await response.json();

      if (response.ok) {
        showMessage(result.message, "success");
        fetchActivities();
      } else {
        if (response.status === 401) {
          teacherCredentials = null;
          updateAuthControls();
          fetchActivities();
        }
        showMessage(result.detail || "An error occurred", "error");
      }
    } catch (error) {
      showMessage("Failed to unregister. Please try again.", "error");
      console.error("Error unregistering:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
          headers: {
            Authorization: authorizationHeader(teacherCredentials),
          },
        }
      );

      const result = await response.json();

      if (response.ok) {
        showMessage(result.message, "success");
        signupForm.reset();
        fetchActivities();
      } else {
        if (response.status === 401) {
          teacherCredentials = null;
          updateAuthControls();
          fetchActivities();
        }
        showMessage(result.detail || "An error occurred", "error");
      }
    } catch (error) {
      showMessage("Failed to sign up. Please try again.", "error");
      console.error("Error signing up:", error);
    }
  });

  loginButton.addEventListener("click", () => loginDialog.showModal());
  cancelLoginButton.addEventListener("click", () => loginDialog.close());

  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const credentials = {
      username: document.getElementById("teacher-username").value,
      password: document.getElementById("teacher-password").value,
    };

    try {
      const response = await fetch("/auth/login", {
        method: "POST",
        headers: {
          Authorization: authorizationHeader(credentials),
        },
      });
      const result = await response.json();

      if (!response.ok) {
        showLoginError(result.detail || "Teacher login failed.");
        return;
      }

      teacherCredentials = credentials;
      loginMessage.textContent = "";
      loginMessage.className = "hidden";
      loginForm.reset();
      loginDialog.close();
      updateAuthControls();
      showMessage(`Logged in as ${result.username}.`, "success");
      fetchActivities();
    } catch (error) {
      showLoginError("Unable to log in. Please try again.");
      console.error("Error logging in:", error);
    }
  });

  logoutButton.addEventListener("click", () => {
    teacherCredentials = null;
    updateAuthControls();
    fetchActivities();
    showMessage("Logged out.", "success");
  });

  // Initialize app
  updateAuthControls();
  fetchActivities();
});
