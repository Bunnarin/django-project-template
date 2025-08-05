from django.shortcuts import render, redirect
from django.urls import reverse, NoReverseMatch
from django.apps import apps

def home_view(request):
    user = request.user
    if not user.is_authenticated:
        return redirect('account_login')
    
    s = request.session
    s['permissions'] = s.get('permissions', [])

    accessible_models_by_app = {}

    excluded_app_labels = [
        'admin',       # Django Admin
        'auth',        # Django Authentication (User, Group, Permission models)
        'contenttypes',# Django ContentTypes
        'sessions',    # Django Sessions
        'static', # Django static
    ]

    # Iterate through all installed apps
    for app_config in apps.get_app_configs():
        if app_config.label in excluded_app_labels:
            continue # Skip this app

        for model_class in app_config.get_models():
            # Skip abstract models, proxy models, or models without list views
            if model_class._meta.abstract or model_class._meta.proxy:
                continue

            app_label = model_class._meta.app_label
            model_name = model_class._meta.model_name
            verbose_name_plural = model_class._meta.verbose_name_plural or f"{model_name}s"
            verbose_name_plural = verbose_name_plural.title()

            has_rud_access = False
            if any(perm in s['permissions'] for perm in [f'change_{model_name}', f'delete_{model_name}', f'view_{model_name}']):
                has_rud_access = True

            has_add_access = False
            if f'add_{model_name}' in s['permissions']:
                has_add_access = True

            # Initialize app section if it doesn't exist
            if app_label not in accessible_models_by_app:
                app_config_obj = apps.get_app_config(app_label)
                accessible_models_by_app[app_label] = {
                    'app_name': app_config_obj.verbose_name or app_label.title(),
                    'models': []
                }

            if has_rud_access:
                try:
                    model_url = reverse(f'{app_label}:view_{model_name}')
                    accessible_models_by_app[app_label]['models'].append({
                        'name': verbose_name_plural,
                        'url': model_url,
                    })
                except NoReverseMatch:
                    pass 
            elif has_add_access: # If no RUD access, check if user can add
                try:
                    model_url = reverse(f'{app_label}:add_{model_name}')
                    accessible_models_by_app[app_label]['models'].append({
                        'name': f'Add {verbose_name_plural}',
                        'url': model_url,
                    })
                except NoReverseMatch:
                    pass

    # Remove apps with no accessible models
    context = {'accessible_models_by_app': {
        app_label: app_data 
        for app_label, app_data in accessible_models_by_app.items() 
        if app_data['models']
    }}
    return render(request, 'home.html', context)