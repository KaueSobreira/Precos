from django.shortcuts import render
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError

from .models import GrupoCanais


class GrupoListView(ListView):
    model = GrupoCanais
    template_name = 'grupo_vendas/grupo_list.html'
    context_object_name = 'grupos'

    def get_queryset(self):
        return GrupoCanais.objects.all().prefetch_related('canais')


class GrupoDetailView(DetailView):
    model = GrupoCanais
    template_name = 'grupo_vendas/grupo_detail.html'
    context_object_name = 'grupo'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['canais'] = self.object.canais.filter(ativo=True)
        return context


class GrupoCreateView(CreateView):
    model = GrupoCanais
    template_name = 'grupo_vendas/grupo_form.html'
    fields = ['nome', 'descricao', 'imposto', 'operacao', 'lucro', 'promocao', 'minimo', 'ads', 'comissao', 'tipo_custo', 'canal_referencia_custo']
    success_url = reverse_lazy('grupo_list')

    def form_valid(self, form):
        messages.success(self.request, 'Grupo criado com sucesso!')
        return super().form_valid(form)


class GrupoUpdateView(UpdateView):
    model = GrupoCanais
    template_name = 'grupo_vendas/grupo_form.html'
    fields = ['nome', 'descricao', 'imposto', 'operacao', 'lucro', 'promocao', 'minimo', 'ads', 'comissao', 'tipo_custo', 'canal_referencia_custo']
    success_url = reverse_lazy('grupo_list')

    def form_valid(self, form):
        messages.success(self.request, 'Grupo atualizado com sucesso!')
        return super().form_valid(form)


class GrupoDeleteView(DeleteView):
    model = GrupoCanais
    template_name = 'grupo_vendas/grupo_confirm_delete.html'
    success_url = reverse_lazy('grupo_list')

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.is_default:
            messages.error(request, 'O grupo padrão ECOSSISTEMA não pode ser excluído.')
            return render(request, self.template_name, {'grupo': self.object, 'is_protected': True})
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        if self.object.is_default:
            messages.error(self.request, 'O grupo padrão ECOSSISTEMA não pode ser excluído.')
            return render(self.request, self.template_name, {'grupo': self.object, 'is_protected': True})
        messages.success(self.request, 'Grupo excluído com sucesso!')
        return super().form_valid(form)
