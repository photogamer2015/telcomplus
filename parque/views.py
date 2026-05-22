from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import EquipoForm, EstadoTicketForm, ReportePublicoForm
from .models import Equipo, TicketSoporte
from .qr import actualizar_qr


def _base_url(request):
    return request.build_absolute_uri('/').rstrip('/')


def _es_admin(user):
    return user.is_superuser or user.groups.filter(name='Admin').exists()


def _puede_eliminar(user):
    return _es_admin(user)


def _puede_editar_equipos(user):
    return _es_admin(user) or user.groups.filter(name='Admin de contrato').exists()


def _puede_modificar_tickets(user):
    return _es_admin(user) or user.groups.filter(name='Tecnico').exists()


def _rol_usuario(user):
    if user.is_superuser:
        return 'Admin'
    group = user.groups.first()
    return group.name if group else 'Sin rol'


def _contexto_panel(request, extra=None):
    context = {
        'rol_usuario': _rol_usuario(request.user),
        'puede_editar_equipos': _puede_editar_equipos(request.user),
        'puede_eliminar': _puede_eliminar(request.user),
        'puede_modificar_tickets': _puede_modificar_tickets(request.user),
    }
    if extra:
        context.update(extra)
    return context


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')


@login_required
def dashboard(request):
    equipos_por_tipo = Equipo.objects.values('tipo').annotate(total=Count('id')).order_by('tipo')
    ultimos_tickets = TicketSoporte.objects.select_related('equipo')[:5]
    context = _contexto_panel(request, {
        'total_equipos': Equipo.objects.count(),
        'total_tickets': TicketSoporte.objects.count(),
        'tickets_nuevos': TicketSoporte.objects.filter(estado=TicketSoporte.NUEVO).count(),
        'equipos_por_tipo': equipos_por_tipo,
        'ultimos_tickets': ultimos_tickets,
    })
    return render(request, 'parque/dashboard.html', context)


@login_required
def equipo_list(request):
    query = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', '').strip()
    equipos = Equipo.objects.all()
    if query:
        equipos = equipos.filter(
            Q(marca__icontains=query)
            | Q(modelo__icontains=query)
            | Q(serie__icontains=query)
            | Q(razon_social_cliente__icontains=query)
            | Q(ciudad__icontains=query)
        )
    if tipo:
        equipos = equipos.filter(tipo=tipo)
    context = _contexto_panel(request, {
        'equipos': equipos,
        'query': query,
        'tipo': tipo,
        'tipos': Equipo.TIPO_CHOICES,
    })
    return render(request, 'parque/equipo_list.html', context)


@login_required
def equipo_detail(request, pk):
    equipo = get_object_or_404(Equipo, pk=pk)
    # Si el QR no está en BD o si el archivo físico se borró (ej. Render efímero)
    if not equipo.qr_code or not equipo.qr_code.storage.exists(equipo.qr_code.name):
        actualizar_qr(equipo, _base_url(request))
    context = _contexto_panel(request, {'equipo': equipo})
    return render(request, 'parque/equipo_detail.html', context)


@login_required
def equipo_create(request):
    if not _puede_editar_equipos(request.user):
        raise PermissionDenied
    if request.method == 'POST':
        form = EquipoForm(request.POST)
        if form.is_valid():
            equipo = form.save(commit=False)
            equipo.creado_por = request.user
            equipo.save()
            actualizar_qr(equipo, _base_url(request))
            messages.success(request, 'Equipo creado y QR generado.')
            return redirect('equipo_detail', pk=equipo.pk)
    else:
        form = EquipoForm()
    context = _contexto_panel(request, {'form': form, 'titulo': 'Crear equipo'})
    return render(request, 'parque/equipo_form.html', context)


@login_required
def equipo_update(request, pk):
    if not _puede_editar_equipos(request.user):
        raise PermissionDenied
    equipo = get_object_or_404(Equipo, pk=pk)
    if request.method == 'POST':
        form = EquipoForm(request.POST, instance=equipo)
        if form.is_valid():
            equipo = form.save()
            actualizar_qr(equipo, _base_url(request))
            messages.success(request, 'Equipo actualizado y QR regenerado.')
            return redirect('equipo_detail', pk=equipo.pk)
    else:
        form = EquipoForm(instance=equipo)
    context = _contexto_panel(request, {'form': form, 'titulo': 'Editar equipo', 'equipo': equipo})
    return render(request, 'parque/equipo_form.html', context)


@login_required
def equipo_qr_download(request, pk):
    equipo = get_object_or_404(Equipo, pk=pk)
    actualizar_qr(equipo, _base_url(request))
    return FileResponse(equipo.qr_code.open('rb'), as_attachment=True, filename=f'QR-{equipo.serie}.png')


@login_required
def ticket_list(request):
    if request.method == 'POST':
        if not _puede_modificar_tickets(request.user):
            raise PermissionDenied
        ticket_id = request.POST.get('ticket_id')
        nuevo_estado = request.POST.get('nuevo_estado')
        if ticket_id and nuevo_estado:
            ticket = get_object_or_404(TicketSoporte, pk=ticket_id)
            ticket.estado = nuevo_estado
            ticket.save()
            messages.success(request, f'Estado del ticket #{ticket.pk} actualizado a {ticket.get_estado_display()}.')
        return redirect(request.META.get('HTTP_REFERER', 'ticket_list'))

    estado = request.GET.get('estado', '').strip()
    tickets = TicketSoporte.objects.select_related('equipo')
    if estado:
        tickets = tickets.filter(estado=estado)
    context = _contexto_panel(request, {
        'tickets': tickets,
        'estado': estado,
        'estados': TicketSoporte.ESTADO_CHOICES,
    })
    return render(request, 'parque/ticket_list.html', context)


@login_required
def ticket_detail(request, pk):
    ticket = get_object_or_404(TicketSoporte.objects.select_related('equipo'), pk=pk)
    if request.method == 'POST':
        if not _puede_modificar_tickets(request.user):
            raise PermissionDenied
        form = EstadoTicketForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            messages.success(request, 'Estado del ticket actualizado.')
            return redirect('ticket_detail', pk=ticket.pk)
    else:
        form = EstadoTicketForm(instance=ticket)
    context = _contexto_panel(request, {'ticket': ticket, 'form': form})
    return render(request, 'parque/ticket_detail.html', context)


@login_required
def equipo_delete(request, pk):
    if not _puede_eliminar(request.user):
        raise PermissionDenied
    equipo = get_object_or_404(Equipo, pk=pk)
    if request.method == 'POST':
        equipo.delete()
        messages.success(request, 'Equipo eliminado correctamente.')
        return redirect('equipo_list')
    context = _contexto_panel(request, {'equipo': equipo, 'titulo': 'Eliminar equipo'})
    return render(request, 'parque/equipo_confirm_delete.html', context)


@login_required
def ticket_delete(request, pk):
    if not _puede_eliminar(request.user):
        raise PermissionDenied
    ticket = get_object_or_404(TicketSoporte, pk=pk)
    if request.method == 'POST':
        ticket.delete()
        messages.success(request, 'Reporte eliminado correctamente.')
        return redirect('ticket_list')
    context = _contexto_panel(request, {'ticket': ticket, 'titulo': 'Eliminar reporte'})
    return render(request, 'parque/ticket_confirm_delete.html', context)


def public_report(request, public_id):
    equipo = get_object_or_404(Equipo, public_id=public_id)
    if request.method == 'POST':
        form = ReportePublicoForm(request.POST)
        if form.is_valid():
            import datetime
            from django.utils import timezone
            
            time_threshold = timezone.now() - datetime.timedelta(minutes=5)
            duplicate = TicketSoporte.objects.filter(
                equipo=equipo,
                nombre_cliente=form.cleaned_data['nombre_cliente'],
                telefono=form.cleaned_data['telefono'],
                empresa=form.cleaned_data['empresa'],
                problema=form.cleaned_data['problema'],
                creado_en__gte=time_threshold
            ).first()
            
            if duplicate:
                request.session['last_ticket_pk'] = duplicate.pk
                return redirect('public_report_success', public_id=equipo.public_id)

            ticket = form.save(commit=False)
            ticket.equipo = equipo
            ticket.save()
            request.session['last_ticket_pk'] = ticket.pk
            return redirect('public_report_success', public_id=equipo.public_id)
    else:
        form = ReportePublicoForm()
    return render(request, 'parque/public_report.html', {'equipo': equipo, 'form': form})

def public_report_success(request, public_id):
    equipo = get_object_or_404(Equipo, public_id=public_id)
    ticket_pk = request.session.get('last_ticket_pk')
    if not ticket_pk:
        return redirect('public_report', public_id=public_id)
    ticket = get_object_or_404(TicketSoporte, pk=ticket_pk, equipo=equipo)
    return render(request, 'parque/report_success.html', {'ticket': ticket, 'equipo': equipo})


@login_required
def reset_ticket_ids(request):
    if not request.user.is_superuser:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
        
    from django.db import connection
    
    if request.method == 'POST':
        # Re-enumerar tickets
        tickets = list(TicketSoporte.objects.all().order_by('id'))
        for i, t in enumerate(tickets, start=1):
            if t.id != i:
                TicketSoporte.objects.filter(id=t.id).update(id=i)
                
        max_id = len(tickets)
        
        # Reiniciar secuencias (Soporta PostgreSQL y SQLite)
        with connection.cursor() as cursor:
            try:
                cursor.execute(f"ALTER SEQUENCE parque_ticketsoporte_id_seq RESTART WITH {max_id + 1};")
            except Exception:
                pass
            try:
                cursor.execute("DELETE FROM sqlite_sequence WHERE name='parque_ticketsoporte'")
            except Exception:
                pass
                
        messages.success(request, f"¡IDs de tickets reordenados! El próximo ticket será el #{max_id + 1}.")
    
    return redirect('ticket_list')
