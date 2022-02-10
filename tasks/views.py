from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.detail import DetailView
from django.forms import ModelForm
from tasks.models import Task
from django.contrib.auth.forms import UserCreationForm

from django.contrib.auth.views import LoginView

from django.contrib.auth.mixins import LoginRequiredMixin


class AuthorisedTaskManager(LoginRequiredMixin):
    def get_queryset(self):
        return Task.objects.filter(deleted=False, user=self.request.user)


class UserLoginView(LoginView):
    template_name = "user_login.html"


class UserCreateView(CreateView):
    form_class = UserCreationForm
    template_name = "user_create.html"
    success_url = "/user/login"


class HomeView(View):
    def get(self, request):
        return render(request, "index.html")


class GenericTaskDeleteView(AuthorisedTaskManager, DeleteView):
    model = Task
    template_name = "task_delete.html"
    success_url = "/tasks"


class GenericTaskDetailView(AuthorisedTaskManager, DetailView):
    model = Task
    template_name = "task_detail.html"
    context_object_name = "taskDetail"


class TaskCreateForm(ModelForm):
    class Meta:
        model = Task
        fields = ["title", "description", "priority", "completed"]

    def check_priority(self, user):
        priority = self.cleaned_data['priority']
        title = self.cleaned_data['title']

       # modifying priority

        def modifyPriority(priority):
            if Task.objects.filter(priority=priority+1, completed=False, user=user).exists():
                priority = priority+1
                modifyPriority(priority)
            else:
                task = Task.objects.get(
                    priority=priority, completed=False, user=user)
                Task(title=task.title, description=task.description,
                     priority=priority+1, user=user).save()
                Task.objects.filter(id=task.id).delete()
        # a check wether the task with same name exist beacuse during marking a task complete it is creating a new task

        def taskCheckExist():
            if Task.objects.filter(priority=priority, completed=False, title=title, user=user):
                return priority
            else:
                while Task.objects.filter(priority=priority, completed=False, user=user).exists():
                    modifyPriority(priority)
                return priority
                # start of process of checking tasks
        taskCheckExist()


class GenericTaskUpdateView(AuthorisedTaskManager, UpdateView):
    model = Task
    form_class = TaskCreateForm
    template_name = "task_operate.html"
    success_url = "/tasks"

    def form_valid(self, form):
        form.check_priority(self.request.user)
        self.object = form.save()
        self.object.user = self.request.user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


class GenericTaskCreateView(AuthorisedTaskManager, CreateView):
    form_class = TaskCreateForm
    template_name = "task_operate.html"
    success_url = "/tasks"

    def form_valid(self, form):
        form.check_priority(self.request.user)
        self.object = form.save()
        self.object.user = self.request.user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


class GenericTaskView(LoginRequiredMixin, ListView):
    queryset = Task.objects.filter(deleted=False)
    template_name = "tasks.html"
    context_object_name = "tasks"
    paginate_by = 10

    def get_queryset(self):
        search_term = self.request.GET.get("search")
        tasks = Task.objects.filter(user=self.request.user)
        if search_term:
            tasks = tasks.filter(title__icontains=search_term)
        return tasks

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['completedTasks'] = Task.objects.filter(
            completed=True, user=self.request.user)
        context['pendingTasks'] = Task.objects.filter(
            completed=False, user=self.request.user)
        context['taskSelected'] = {
            "selected": self.request.GET.get("taskSelected") if self.request.GET.get("taskSelected") else "All"}
        return context
