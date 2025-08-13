from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.forms import formset_factory, inlineformset_factory
from django.shortcuts import render
from django.forms.models import modelform_factory
from django.shortcuts import redirect
from .forms import get_default_form

class BaseDetailView(PermissionRequiredMixin, DetailView):
    """
    Base view for displaying a single object.
    """
    template_name = 'core/generic_list.html'
    fields = []

    def get_permission_required(self):
        """
        can view if has any one of the read, change, delete permission
        """
        user = self.request.user
        self.app_label = self.model._meta.app_label
        self.model_name = self.model._meta.model_name
        for action in ["view", "change", "delete"]:
            if user.has_perm(f'{self.app_label}.{action}_{self.model_name}'):
                return [f'{self.app_label}.{action}_{self.model_name}']
        return [f'{self.app_label}.view_{self.model_name}']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['fields'] = self.fields
        return context

class BaseListView(PermissionRequiredMixin, ListView):
    """
    Base view for displaying a list of objects.
    """
    object_actions = []
    actions = []
    template_name = 'core/generic_list.html'
    table_fields = []

    def get_permission_required(self):
        """
        can view if has any one of the read, change, delete permission
        """
        user = self.request.user
        self.app_label = self.model._meta.app_label
        self.model_name = self.model._meta.model_name
        for action in ["view", "change", "delete"]:
            if user.has_perm(f'{self.app_label}.{action}_{self.model_name}'):
                return [f'{self.app_label}.{action}_{self.model_name}']
        return [f'{self.app_label}.view_{self.model_name}']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        # filter the action perm
        context["object_actions"] = {}
        for action, url, permission in self.object_actions:
            # it can be None for when this view can derive the permission on its own
            if not permission:
                permission = url.replace(':', '.')
            if user.has_perm(permission):
                context["object_actions"][action] = url
        
        # filter the action perm
        context["actions"] = {}
        for action, url, permission in self.actions:
            # it can be None for when this view can derive the permission on its own
            if not permission:
                permission = url.replace(':', '.')
            if user.has_perm(permission):
                context["actions"][action] = url

        context['table_fields'] = self.table_fields
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        # Get all potential foreign key fields from table_fields
        related_fields = set()
        for field in getattr(self, 'table_fields', []):
            # Add direct fields that might be foreign keys
            field = field.replace('.', '__')
            direct_field = field.split('__')[0]
            try: field_obj = self.model._meta.get_field(direct_field)
            except: continue
            direct_field_is_relation = field_obj.is_relation and field_obj.many_to_one and field_obj.concrete
            
            if direct_field_is_relation:
                related_fields.add(direct_field)

            if ("__" in field) and direct_field_is_relation:
                # check if the chained field is also a relation
                field_model = field_obj.related_model
                chained_obj = field_model._meta.get_field(field.split('__')[1])
                if chained_obj.is_relation and chained_obj.many_to_one and chained_obj.concrete:
                    related_fields.add(field)
            
        # Apply select_related if we have any related fields
        if related_fields:
            queryset = queryset.select_related(*related_fields)
        
        return queryset

class BaseWriteView(PermissionRequiredMixin):
    pk_url_kwarg = 'pk'
    template_name = 'core/generic_form.html'

    def get_success_url(self):
        return reverse_lazy(f'{self.app_label}:view_{self.model_name}')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.model_name
        context['cancel_url'] = reverse_lazy(f'{self.app_label}:view_{self.model_name}')
        return context

class BaseCreateView(BaseWriteView, CreateView):
    def get_permission_required(self):
        self.app_label = self.model._meta.app_label
        self.model_name = self.model._meta.model_name
        return [f'{self.app_label}.add_{self.model_name}']
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class BaseUpdateView(BaseWriteView, UpdateView):
    def get_permission_required(self):
        self.app_label = self.model._meta.app_label
        self.model_name = self.model._meta.model_name
        return [f'{self.app_label}.change_{self.model_name}']

class BaseDeleteView(BaseWriteView, DeleteView):
    def get_permission_required(self):
        self.app_label = self.model._meta.app_label
        self.model_name = self.model._meta.model_name
        return [f'{self.app_label}.delete_{self.model_name}']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Delete {self.object}?"
        return context

class BaseImportView(BaseCreateView):
    """
    Mixin for views that require permission to import an object.
    first, it will give a model form that asks the user to fill out the default value of each field.
    they can also paste an entire row of values where x is the row number
    then once they submit, we give them another form that autogenerate x amount of form (in row format)
    those rows of form comes with prefilled default that they input and they can modify it
    finally, they can submit the form and it will bulk create all the objects
    """
    fields = []
    
    def get(self, request, *args, **kwargs):
        default_form = get_default_form(self.fields, self.model)()
        return render(request, self.template_name, {'form': default_form, 'title': 'set the default values'})
    
    def post(self, request, *args, **kwargs):
        FormSet_Class = formset_factory(
            self.form_class or modelform_factory(self.model, fields='__all__'),
            extra=0, can_delete=True
        )
        if 'form-TOTAL_FORMS' not in request.POST:
            form = get_default_form(self.fields, self.model)(request.POST)
            if form.is_valid():
                # calculating the num form
                data = form.cleaned_data
                max_row_num = 0
                for field in form.fields:
                    try: data[field] = data[field].split('\n')
                    except: continue
                    max_row_num = max(max_row_num, len(data[field]))
                
                # now populating the inital 
                initials = []         
                for i in range(max_row_num):
                    initials.append({})
                    for field in form.fields:
                        # if cleaned_data is an array, use the indexed. else, just use its default value
                        if isinstance(data[field], list) and len(data[field]) > 1:
                            try: initials[i][field] = data[field][i]
                            except IndexError: continue    
                        elif isinstance(data[field], list) and len(data[field]) == 1:
                            initials[i][field] = data[field][0]
                        else:
                            initials[i][field] = data[field]

                formset = FormSet_Class(initial=initials)
                return render(request, self.template_name, {'formset': formset})
            return render(request, self.template_name, {'form': form})
        
        elif 'form-TOTAL_FORMS' in request.POST:
            formset = FormSet_Class(request.POST)
            instances = []
            if formset.is_valid():
                for form in formset:
                    instance = form.save(commit=False)
                    instance.clean()
                    instances.append(instance)
                self.model.objects.bulk_create(instances)   
            else:
                return render(request, self.template_name, {'formset': formset})
        return redirect(f'{self.app_label}:view_{self.model_name}')

class BaseInlineCreateView(BaseCreateView):
    """
    this is like extra_view's but for createview cuz that sht doesnt handle creation at all
    """
    model = None
    fields = '__all__'
    form_class = None
    inline_model = None
    inline_form_class = None
    inline_fields = '__all__'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.inline_form_class:
            context['formset'] = inlineformset_factory(self.model, self.inline_model, form=self.inline_form_class, fields=self.inline_fields)(self.request.POST or None)
        else:
            context['formset'] = inlineformset_factory(self.model, self.inline_model, fields=self.inline_fields)(self.request.POST or None)
        return context    
    
    # after the part where we create the main model, we create the inline models
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if formset.is_valid():
            form.instance.created_by = self.request.user
            self.object = form.save()
            instances = formset.save(commit=False)
            for instance in instances:
                setattr(instance, self.model.__name__.lower(), self.object)
                instance.save()
            return super().form_valid(form)
        return self.form_invalid(form)