from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q

from .models import Componente

@login_required
def buscar_componente_api(request):
    """
    API para buscar componentes por nome.
    Retorna JSON: [{'label': 'Nome', 'value': 'Preço'}, ...]
    """
    term = request.GET.get('term', '')
    if len(term) < 2:
        return JsonResponse([], safe=False)

    componentes = Componente.objects.filter(
        nome__icontains=term, 
        ativo=True
    ).order_by('nome')[:20]

    results = []
    for comp in componentes:
        results.append({
            'label': comp.nome,
            'price': float(comp.preco)  # Retorna float para facilitar JS, formatar depois
        })
    
    return JsonResponse(results, safe=False)

# --- CRUD Views ---

class ComponenteListView(LoginRequiredMixin, ListView):
    model = Componente
    template_name = 'controle_producao/componente_list.html'
    context_object_name = 'componentes'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(nome__icontains=search)
        return queryset.order_by('nome')

class ComponenteCreateView(LoginRequiredMixin, CreateView):
    model = Componente
    template_name = 'controle_producao/componente_form.html'
    fields = ['nome', 'preco', 'ativo']
    success_url = reverse_lazy('componente_list')

    def form_valid(self, form):
        messages.success(self.request, 'Componente criado com sucesso!')
        return super().form_valid(form)

class ComponenteUpdateView(LoginRequiredMixin, UpdateView):
    model = Componente
    template_name = 'controle_producao/componente_form.html'
    fields = ['nome', 'preco', 'ativo']
    success_url = reverse_lazy('componente_list')

    def form_valid(self, form):
        messages.success(self.request, 'Componente atualizado com sucesso!')
        return super().form_valid(form)

class ComponenteDeleteView(LoginRequiredMixin, DeleteView):
    model = Componente
    template_name = 'controle_producao/componente_confirm_delete.html'
    success_url = reverse_lazy('componente_list')

    def form_valid(self, form):
        messages.success(self.request, 'Componente excluído com sucesso!')
        return super().form_valid(form)
