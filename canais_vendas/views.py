from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy, reverse

from .models import CanalVenda
from grupo_vendas.models import GrupoCanais
from tabela_frete.models import TabelaFrete, TabelaTaxa


# Views de Canais de Venda
class CanalListView(ListView):
    model = CanalVenda
    template_name = 'canais_vendas/canal_list.html'
    context_object_name = 'canais'

    def get_queryset(self):
        queryset = CanalVenda.objects.select_related('grupo', 'tabela_frete')

        grupo = self.request.GET.get('grupo')
        if grupo:
            queryset = queryset.filter(grupo_id=grupo)

        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(nome__icontains=search)

        return queryset.order_by('grupo__nome', 'nome')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grupos'] = GrupoCanais.objects.all()
        return context


class CanalDetailView(DetailView):
    model = CanalVenda
    template_name = 'canais_vendas/canal_detail.html'
    context_object_name = 'canal'


class CanalCreateView(CreateView):
    model = CanalVenda
    template_name = 'canais_vendas/canal_form.html'
    fields = [
        'nome', 'grupo', 'descricao', 'ativo', 'herdar_grupo',
        'imposto', 'operacao', 'lucro', 'promocao', 'minimo', 'ads', 'comissao',
        'tipo_frete', 'frete_fixo', 'tabela_frete', 'tabela_taxa', 'nota_vendedor'
    ]
    success_url = reverse_lazy('canal_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grupos'] = GrupoCanais.objects.all()
        context['tabelas_frete'] = TabelaFrete.objects.filter(ativo=True)
        context['tabelas_taxa'] = TabelaTaxa.objects.filter(ativo=True)
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Canal criado com sucesso!')
        return super().form_valid(form)


class CanalUpdateView(UpdateView):
    model = CanalVenda
    template_name = 'canais_vendas/canal_form.html'
    fields = [
        'nome', 'grupo', 'descricao', 'ativo', 'herdar_grupo',
        'imposto', 'operacao', 'lucro', 'promocao', 'minimo', 'ads', 'comissao',
        'tipo_frete', 'frete_fixo', 'tabela_frete', 'tabela_taxa', 'nota_vendedor'
    ]

    def get_success_url(self):
        return reverse('canal_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grupos'] = GrupoCanais.objects.all()
        context['tabelas_frete'] = TabelaFrete.objects.filter(ativo=True)
        context['tabelas_taxa'] = TabelaTaxa.objects.filter(ativo=True)
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Canal atualizado com sucesso!')
        return super().form_valid(form)


class CanalDeleteView(DeleteView):
    model = CanalVenda
    template_name = 'canais_vendas/canal_confirm_delete.html'
    success_url = reverse_lazy('canal_list')

    def form_valid(self, form):
        messages.success(self.request, 'Canal excluído com sucesso!')
        return super().form_valid(form)