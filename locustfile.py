from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks

    @task(3)  # Weight 3 - most common
    def index(self):
        self.client.get("/")

    @task(2)
    def login_page(self):
        self.client.get("/login")

    @task(1)
    def register_page(self):
        self.client.get("/register")

    @task(1)
    def materials(self):
        self.client.get("/materials")

    @task(1)
    def research(self):
        self.client.get("/research")

    @task(1)
    def ebooks(self):
        self.client.get("/ebooks")

    @task(1)
    def journals(self):
        self.client.get("/journals")

    @task(1)
    def events(self):
        self.client.get("/events")