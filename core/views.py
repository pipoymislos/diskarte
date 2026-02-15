from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import timedelta, datetime
from django import forms
from .models import Product, Category, StockMovement, ActivityLog
from .forms import LoginForm, ProductForm, CategoryForm, StockMovementForm
from .decorators import single_admin_required


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                
                ActivityLog.objects.create(
                    user=user,
                    action='LOGIN',
                    model_name='User',
                    object_id=user.id,
                    object_repr=user.username,
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                
                messages.success(request, f'Welcome back, {username}!')
                return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    
    return render(request, 'login.html', {'form': form})


@login_required
@single_admin_required
def logout_view(request):
    if request.user.is_authenticated:
        ActivityLog.objects.create(
            user=request.user,
            action='LOGOUT',
            model_name='User',
            object_id=request.user.id,
            object_repr=request.user.username,
            ip_address=request.META.get('REMOTE_ADDR')
        )
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


@login_required
@single_admin_required
def dashboard(request):
    total_products = Product.objects.count()
    total_categories = Category.objects.count()
    low_stock_products = Product.objects.filter(quantity__lte=F('reorder_level')).count()
    out_of_stock = Product.objects.filter(quantity=0).count()
    total_stock_value = Product.objects.aggregate(total=Sum(F('quantity') * F('price')))['total'] or 0
    
    recent_activities = ActivityLog.objects.all()[:10]
    low_stock_items = Product.objects.filter(quantity__lte=F('reorder_level')).order_by('quantity')[:5]
    recent_movements = StockMovement.objects.select_related('product').all()[:5]
    
    top_products = Product.objects.annotate(
        stock_value=F('quantity') * F('price')
    ).order_by('-stock_value')[:5]
    
    last_7_days = []
    stock_in_data = []
    stock_out_data = []
    
    for i in range(6, -1, -1):
        date = timezone.now().date() - timedelta(days=i)
        last_7_days.append(date.strftime('%b %d'))
        
        stock_in = StockMovement.objects.filter(
            movement_type='IN',
            date__date=date
        ).aggregate(total=Sum('quantity'))['total'] or 0
        stock_in_data.append(stock_in)
        
        stock_out = StockMovement.objects.filter(
            movement_type='OUT',
            date__date=date
        ).aggregate(total=Sum('quantity'))['total'] or 0
        stock_out_data.append(stock_out)
    
    context = {
        'total_products': total_products,
        'total_categories': total_categories,
        'low_stock_products': low_stock_products,
        'out_of_stock': out_of_stock,
        'total_stock_value': total_stock_value,
        'recent_activities': recent_activities,
        'low_stock_items': low_stock_items,
        'recent_movements': recent_movements,
        'top_products': top_products,
        'chart_labels': last_7_days,
        'stock_in_data': stock_in_data,
        'stock_out_data': stock_out_data,
    }
    return render(request, 'dashboard.html', context)


@login_required
@single_admin_required
def product_list(request):
    products = Product.objects.select_related('category').all()
    categories = Category.objects.all()
    
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(sku__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )
    
    category_filter = request.GET.get('category', '')
    if category_filter:
        products = products.filter(category_id=category_filter)
    
    stock_status = request.GET.get('stock_status', '')
    if stock_status == 'low':
        products = products.filter(quantity__lte=F('reorder_level'), quantity__gt=0)
    elif stock_status == 'out':
        products = products.filter(quantity=0)
    elif stock_status == 'in':
        products = products.filter(quantity__gt=F('reorder_level'))
    
    context = {
        'products': products,
        'categories': categories,
        'search_query': search_query,
        'category_filter': category_filter,
        'stock_status': stock_status,
    }
    return render(request, 'inventory/product_list.html', context)


@login_required
@single_admin_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    stock_movements = StockMovement.objects.filter(product=product)[:10]
    
    context = {
        'product': product,
        'stock_movements': stock_movements,
    }
    return render(request, 'inventory/product_detail.html', context)


@login_required
@single_admin_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            
            ActivityLog.objects.create(
                user=request.user,
                action='CREATE',
                model_name='Product',
                object_id=product.id,
                object_repr=product.name,
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, f'Product "{product.name}" created successfully!')
            return redirect('product_list')
    else:
        form = ProductForm()
    
    return render(request, 'inventory/product_form.html', {'form': form, 'title': 'Add Product'})


@login_required
@single_admin_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            
            ActivityLog.objects.create(
                user=request.user,
                action='UPDATE',
                model_name='Product',
                object_id=product.id,
                object_repr=product.name,
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, f'Product "{product.name}" updated successfully!')
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'inventory/product_form.html', {'form': form, 'title': 'Edit Product'})


@login_required
@single_admin_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        product_name = product.name
        
        ActivityLog.objects.create(
            user=request.user,
            action='DELETE',
            model_name='Product',
            object_id=product.id,
            object_repr=product.name,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        product.delete()
        messages.success(request, f'Product "{product_name}" deleted successfully!')
        return redirect('product_list')
    
    return render(request, 'inventory/product_confirm_delete.html', {'product': product})


@login_required
@single_admin_required
def stock_in(request):
    if request.method == 'POST':
        form = StockMovementForm(request.POST)
        if form.is_valid():
            movement = form.save(commit=False)
            movement.movement_type = 'IN'
            movement.performed_by = request.user
            movement.save()
            
            product = movement.product
            product.quantity += movement.quantity
            product.save()
            
            ActivityLog.objects.create(
                user=request.user,
                action='STOCK_IN',
                model_name='Product',
                object_id=product.id,
                object_repr=product.name,
                changes=f"Added {movement.quantity} {product.unit}",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, f'Stock in completed for {product.name}')
            return redirect('product_list')
    else:
        form = StockMovementForm(initial={'movement_type': 'IN'})
        form.fields['movement_type'].widget = forms.HiddenInput()
    
    return render(request, 'inventory/stock_form.html', {'form': form, 'title': 'Stock In'})


@login_required
@single_admin_required
def stock_out(request):
    if request.method == 'POST':
        form = StockMovementForm(request.POST)
        if form.is_valid():
            movement = form.save(commit=False)
            movement.movement_type = 'OUT'
            
            product = movement.product
            if product.quantity < movement.quantity:
                messages.error(request, f'Not enough stock! Available: {product.quantity} {product.unit}')
                return render(request, 'inventory/stock_form.html', {'form': form, 'title': 'Stock Out'})
            
            movement.price_at_movement = product.price
            movement.total_value = movement.quantity * product.price
            movement.performed_by = request.user
            movement.save()
            
            product.quantity -= movement.quantity
            product.save()
            
            ActivityLog.objects.create(
                user=request.user,
                action='STOCK_OUT',
                model_name='Product',
                object_id=product.id,
                object_repr=product.name,
                changes=f"Removed {movement.quantity} {product.unit} worth ₱{movement.total_value}",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, f'Stock out completed for {product.name} (₱{movement.total_value})')
            return redirect('product_list')
    else:
        form = StockMovementForm(initial={'movement_type': 'OUT'})
        form.fields['movement_type'].widget = forms.HiddenInput()
    
    return render(request, 'inventory/stock_form.html', {'form': form, 'title': 'Stock Out'})


@login_required
@single_admin_required
def activity_log(request):
    logs = ActivityLog.objects.select_related('user').all()
    
    action_filter = request.GET.get('action', '')
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if date_from:
        logs = logs.filter(timestamp__date__gte=datetime.strptime(date_from, '%Y-%m-%d').date())
    if date_to:
        logs = logs.filter(timestamp__date__lte=datetime.strptime(date_to, '%Y-%m-%d').date())
    
    actions = ActivityLog.objects.values_list('action', flat=True).distinct()
    
    context = {
        'logs': logs,
        'actions': actions,
        'action_filter': action_filter,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'reports/activity_log.html', context)


@login_required
@single_admin_required
def inventory_report(request):
    products = Product.objects.select_related('category').all()
    total_inventory_value = products.aggregate(total=Sum(F('quantity') * F('price')))['total'] or 0
    total_items = products.aggregate(total=Sum('quantity'))['total'] or 0
    
    today = timezone.now().date()
    first_day_of_month = today.replace(day=1)
    first_day_of_year = today.replace(month=1, day=1)
    
    stock_out_today = StockMovement.objects.filter(
        movement_type='OUT',
        date__date=today
    ).aggregate(total=Sum('total_value'))['total'] or 0
    
    stock_out_this_month = StockMovement.objects.filter(
        movement_type='OUT',
        date__date__gte=first_day_of_month
    ).aggregate(total=Sum('total_value'))['total'] or 0
    
    stock_out_this_year = StockMovement.objects.filter(
        movement_type='OUT',
        date__date__gte=first_day_of_year
    ).aggregate(total=Sum('total_value'))['total'] or 0
    
    stock_out_all_time = StockMovement.objects.filter(
        movement_type='OUT'
    ).aggregate(total=Sum('total_value'))['total'] or 0
    
    stock_out_by_category = []
    for category in Category.objects.all():
        category_stock_out = StockMovement.objects.filter(
            movement_type='OUT',
            product__category=category
        ).aggregate(
            total_qty=Sum('quantity'),
            total_val=Sum('total_value')
        )
        
        if category_stock_out['total_val'] and category_stock_out['total_val'] > 0:
            stock_out_by_category.append({
                'category': category.name,
                'quantity': category_stock_out['total_qty'] or 0,
                'value': category_stock_out['total_val'] or 0,
            })
    
    recent_stock_outs = StockMovement.objects.filter(
        movement_type='OUT'
    ).select_related('product', 'performed_by').order_by('-date')[:10]
    
    category_summary = []
    for category in Category.objects.all():
        category_products = products.filter(category=category)
        total_qty = category_products.aggregate(total=Sum('quantity'))['total'] or 0
        total_cat_value = category_products.aggregate(total=Sum(F('quantity') * F('price')))['total'] or 0
        product_count = category_products.count()
        
        if product_count > 0 or total_qty > 0:
            category_summary.append({
                'category': category,
                'product_count': product_count,
                'total_quantity': total_qty,
                'total_value': total_cat_value,
            })
    
    context = {
        'products': products,
        'total_inventory_value': total_inventory_value,
        'total_items': total_items,
        'category_summary': category_summary,
        'stock_out_today': stock_out_today,
        'stock_out_this_month': stock_out_this_month,
        'stock_out_this_year': stock_out_this_year,
        'stock_out_all_time': stock_out_all_time,
        'stock_out_by_category': stock_out_by_category,
        'recent_stock_outs': recent_stock_outs,
        'today': today,
        'current_month': today.strftime('%B %Y'),
        'current_year': today.year,
    }
    return render(request, 'reports/inventory_report.html', context)


@login_required
@single_admin_required
def stock_out_report(request):
    stock_outs = StockMovement.objects.filter(movement_type='OUT').select_related('product', 'performed_by')
    
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if date_from:
        stock_outs = stock_outs.filter(date__date__gte=datetime.strptime(date_from, '%Y-%m-%d').date())
    if date_to:
        stock_outs = stock_outs.filter(date__date__lte=datetime.strptime(date_to, '%Y-%m-%d').date())
    
    total_quantity = stock_outs.aggregate(total=Sum('quantity'))['total'] or 0
    total_value = stock_outs.aggregate(total=Sum('total_value'))['total'] or 0
    
    product_summary = []
    for item in stock_outs.values('product__name', 'product__sku').annotate(
        total_qty=Sum('quantity'),
        total_val=Sum('total_value')
    ).order_by('-total_val'):
        product_summary.append({
            'name': item['product__name'],
            'sku': item['product__sku'],
            'quantity': item['total_qty'],
            'value': item['total_val'],
        })
    
    context = {
        'stock_outs': stock_outs,
        'total_quantity': total_quantity,
        'total_value': total_value,
        'product_summary': product_summary,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'reports/stock_out_report.html', context)