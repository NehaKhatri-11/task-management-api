
const API_URL = "http://127.0.0.1:8000";

const token = localStorage.getItem("access_token");

const LIMIT = 5;

let currentPage = 1;
let totalTasks = 0;
let currentSearch = "";
let currentStatus = "";
let currentSortOrder = -1;
let editingTaskId = null;


// CHECK LOGIN
if (!token) {
    window.location.href = "login.html";
}


// HTML ELEMENTS
const taskForm = document.getElementById("taskForm");
const tasksList = document.getElementById("tasksList");

const titleInput = document.getElementById("title");
const descriptionInput = document.getElementById("description");
const statusInput = document.getElementById("status");
const dueDateInput = document.getElementById("due_date");

const taskMessage = document.getElementById("taskMessage");

const formTitle = document.getElementById("formTitle");
const saveTaskButton = document.getElementById("saveTaskButton");
const cancelEditButton = document.getElementById("cancelEditButton");

const searchInput = document.getElementById("searchInput");
const searchButton = document.getElementById("searchButton");
const clearSearchButton = document.getElementById("clearSearchButton");

const statusFilter = document.getElementById("statusFilter");
const sortOrder = document.getElementById("sortOrder");

const prevButton = document.getElementById("prevButton");
const nextButton = document.getElementById("nextButton");
const pageInfo = document.getElementById("pageInfo");

const logoutButton = document.getElementById("logoutButton");


// API REQUEST
async function apiRequest(url, options = {}) {

    const response = await fetch(url, {
        ...options,
        headers: {
            ...options.headers,
            "Authorization": `Bearer ${token}`
        }
    });

    if (response.status === 401) {
        localStorage.removeItem("access_token");
        window.location.href = "login.html";
        throw new Error("Session expired. Please login again.");
    }

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || "Something went wrong");
    }

    return data;
}


// GET ALL TASKS
async function loadTasks() {

    try {
        const params = new URLSearchParams();

        params.append("page", currentPage);
        params.append("limit", LIMIT);
        params.append("sort_order", currentSortOrder);

        if (currentSearch) {
            params.append("search", currentSearch);
        }

        if (currentStatus) {
            params.append("status_filter", currentStatus);
        }

        const data = await apiRequest(
            `${API_URL}/tasks?${params.toString()}`
        );

        totalTasks = data.total_tasks;

        renderTasks(data.tasks);

        const totalPages = Math.max(1, Math.ceil(totalTasks / LIMIT));

        pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;

        prevButton.disabled = currentPage === 1;
        nextButton.disabled = currentPage >= totalPages;

    } catch (error) {
        tasksList.textContent = error.message;
    }
}


// DISPLAY TASKS
function renderTasks(tasks) {

    tasksList.innerHTML = "";

    if (tasks.length === 0) {
        tasksList.textContent = "No tasks found.";
        return;
    }

    tasks.forEach(task => {

        const card = document.createElement("div");
        card.className = "task-card";

        const heading = document.createElement("h3");
        heading.textContent = task.title;

        const description = document.createElement("p");
        description.textContent = task.description || "No description";

        // ATTRACTIVE STATUS BADGE
        const status = document.createElement("span");

        status.className = "status-badge " +
            task.status.toLowerCase().replace(" ", "-");

        status.textContent = task.status;

        const dueDate = document.createElement("p");
        dueDate.className = "due-date";
        dueDate.textContent = `Due Date: ${task.due_date || "Not set"}`;

        const editButton = document.createElement("button");
        editButton.textContent = "Edit";
        editButton.className = "edit-btn";

        editButton.addEventListener("click", () => {
            editTask(task);
        });

        const deleteButton = document.createElement("button");
        deleteButton.textContent = "Delete";
        deleteButton.className = "delete-btn";

        deleteButton.addEventListener("click", () => {
            deleteTask(task.id);
        });

        card.appendChild(heading);
        card.appendChild(description);
        card.appendChild(status);
        card.appendChild(dueDate);
        card.appendChild(editButton);
        card.appendChild(deleteButton);

        tasksList.appendChild(card);
    });
}


// ADD AND UPDATE TASK
taskForm.addEventListener("submit", async function (event) {

    event.preventDefault();

    const taskData = {
        title: titleInput.value.trim(),
        description: descriptionInput.value.trim(),
        status: statusInput.value,
        due_date: dueDateInput.value || ""
    };

    try {

        if (editingTaskId) {

            await apiRequest(`${API_URL}/tasks/${editingTaskId}`, {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(taskData)
            });

            taskMessage.textContent = "Task updated successfully!";

        } else {

            await apiRequest(`${API_URL}/tasks`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(taskData)
            });

            taskMessage.textContent = "Task added successfully!";
        }

        taskMessage.style.color = "green";

        resetForm();

        currentPage = 1;

        await loadTasks();

    } catch (error) {
        taskMessage.textContent = error.message;
        taskMessage.style.color = "red";
    }
});


// EDIT TASK
function editTask(task) {

    editingTaskId = task.id;

    titleInput.value = task.title;
    descriptionInput.value = task.description || "";
    statusInput.value = task.status;
    dueDateInput.value = task.due_date || "";

    formTitle.textContent = "Update Task";
    saveTaskButton.textContent = "Update Task";

    cancelEditButton.style.display = "inline-block";

    taskMessage.textContent = "";

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}


// RESET FORM
function resetForm() {

    taskForm.reset();

    editingTaskId = null;

    formTitle.textContent = "Add New Task";
    saveTaskButton.textContent = "Add Task";

    cancelEditButton.style.display = "none";
}


// CANCEL EDIT
cancelEditButton.addEventListener("click", function () {

    resetForm();
    taskMessage.textContent = "";
});


// DELETE TASK
async function deleteTask(taskId) {

    const confirmDelete = confirm("Are you sure you want to delete this task?");

    if (!confirmDelete) {
        return;
    }

    try {

        await apiRequest(`${API_URL}/tasks/${taskId}`, {
            method: "DELETE"
        });

        taskMessage.textContent = "Task deleted successfully!";
        taskMessage.style.color = "green";

        const totalPages = Math.max(1, Math.ceil((totalTasks - 1) / LIMIT));

        if (currentPage > totalPages) {
            currentPage = totalPages;
        }

        await loadTasks();

    } catch (error) {
        taskMessage.textContent = error.message;
        taskMessage.style.color = "red";
    }
}


// SEARCH
searchButton.addEventListener("click", function () {

    currentSearch = searchInput.value.trim();
    currentPage = 1;

    loadTasks();
});


// CLEAR SEARCH
clearSearchButton.addEventListener("click", function () {

    searchInput.value = "";
    currentSearch = "";
    currentPage = 1;

    loadTasks();
});


// FILTER BY STATUS
statusFilter.addEventListener("change", function () {

    currentStatus = statusFilter.value;
    currentPage = 1;

    loadTasks();
});


// SORT TASKS
sortOrder.addEventListener("change", function () {

    currentSortOrder = Number(sortOrder.value);
    currentPage = 1;

    loadTasks();
});


// PREVIOUS PAGE
prevButton.addEventListener("click", function () {

    if (currentPage > 1) {
        currentPage--;
        loadTasks();
    }
});


// NEXT PAGE
nextButton.addEventListener("click", function () {

    const totalPages = Math.ceil(totalTasks / LIMIT);

    if (currentPage < totalPages) {
        currentPage++;
        loadTasks();
    }
});


// LOGOUT
logoutButton.addEventListener("click", async function () {

    try {

        await apiRequest(`${API_URL}/auth/logout`, {
            method: "POST"
        });

    } catch (error) {
        console.log(error.message);

    } finally {

        localStorage.removeItem("access_token");
        window.location.href = "login.html";
    }
});


// LOAD TASKS
loadTasks();
