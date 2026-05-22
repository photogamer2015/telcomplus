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


def _puede_editar_equipos(user):
    return user.is_superuser or user.groups.filter(name__in=['Admin', 'Admin de contrato']).exists()


def _rol_usuario(user):
    if user.is_superuser:
        return 'Admin'
    group = user.groups.first()
    return group.name if group else 'Sin rol'


def _contexto_panel(request, extra=None):
    context = {
        'rol_usuario': _rol_usuario(request.user),
        'puede_editar_equipos': _puede_editar_equipos(request.user),
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
    if not equipo.qr_code:
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
        form = EstadoTicketForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            messages.success(request, 'Estado del ticket actualizado.')
            return redirect('ticket_detail', pk=ticket.pk)
    else:
        form = EstadoTicketForm(instance=ticket)
    context = _contexto_panel(request, {'ticket': ticket, 'form': form})
    return render(request, 'parque/ticket_detail.html', context)


def public_report(request, public_id):
    equipo = get_object_or_404(Equipo, public_id=public_id)
    if request.method == 'POST':
        form = ReportePublicoForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.equipo = equipo
            ticket.save()
            return render(request, 'parque/report_success.html', {'ticket': ticket, 'equipo': equipo})
    else:
        form = ReportePublicoForm()
    return render(request, 'parque/public_report.html', {'equipo': equipo, 'form': form})

# Create your views here.
