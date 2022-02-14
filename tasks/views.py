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

   # Applied soft deletion

    def form_valid(self, form):
        success_url = self.get_success_url()
        self.object.deleted = True
        self.object.save()
        return HttpResponseRedirect(success_url)


class GenericTaskDetailView(AuthorisedTaskManager, DetailView):
    model = Task
    template_name = "task_detail.html"
    context_object_name = "taskDetail"


class TaskCreateForm(ModelForm):
    class Meta:
        model = Task
        fields = ["title", "description", "priority", "completed"]

     # this function checks wether there is a existing priority if its there then it increses by 1
     # also a status is passed for operation related to task update after addition

    def checkandupdate_Priority(self, user, status):
        priority = self.cleaned_data['priority']
        task_to_be_updated = []
        task = False

        # a check during task updation which states that
        # 1) Task exist already and now user has some update in it
        # 2) It specifies that user has not updated the priority so it can go with normal updation
        #    without running the priority increase algorithm

        if(status == 1):
            return False

        # priority increase algorithm

        try:
            task = Task.objects.get(
                priority=priority, completed=False, deleted=False, user=user)
        except:
            task = False

        while task != False:
            task_to_be_updated.append(task)
            priority = priority+1
            try:
                task = Task.objects.get(
                    priority=priority, completed=False, deleted=False, user=user)
            except:
                task = False

         # after we got the list of tasks whose priority is needed to be updated we update it.

        if len(task_to_be_updated) > 0:
            for task in task_to_be_updated:
                task.priority += 1
            return task_to_be_updated
        else:
            return False


class GenericTaskUpdateView(AuthorisedTaskManager, UpdateView):
    model = Task
    form_class = TaskCreateForm
    template_name = "task_operate.html"
    success_url = "/tasks"

    def form_valid(self, form):

        status = 0

        # here it is a check if a task is updated then while updating it should not run the
        # priority increase algorithm (status=1) it should run it only when user is changing the priority (status=0)

        currenttask = Task.objects.get(id=self.object.id)
        if currenttask.priority == self.object.priority:
            status = 1

        task_tobeUpdated = form.checkandupdate_Priority(
            self.request.user, status)
        if(task_tobeUpdated != False):
            Task.objects.bulk_update(task_tobeUpdated, ['priority'])
        self.object = form.save()
        self.object.user = self.request.user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


class GenericTaskCreateView(AuthorisedTaskManager, CreateView):
    form_class = TaskCreateForm
    template_name = "task_operate.html"
    success_url = "/tasks"

    def form_valid(self, form):

        # get the list which contains the tasks whoose priority are updated so that we can go for bulkupdate

        task_tobeUpdated = form.checkandupdate_Priority(
            self.request.user, status=0)

        # a condition whether to go for bulkupdate or not on basis of task priority existence

        if(task_tobeUpdated != False):
            Task.objects.bulk_update(task_tobeUpdated, ['priority'])

        # normal prodedure as follows to add task

        self.object = form.save()
        self.object.user = self.request.user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


class GenericTaskView(AuthorisedTaskManager, ListView):
    template_name = "tasks.html"
    context_object_name = "tasks"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['completedTasks'] = Task.objects.filter(
            completed=True, deleted=False, user=self.request.user)
        context['pendingTasks'] = Task.objects.filter(
            completed=False, deleted=False, user=self.request.user)
        context['taskSelected'] = {
            "selected": self.request.GET.get("taskSelected") if self.request.GET.get("taskSelected") else "All"}
        return context
