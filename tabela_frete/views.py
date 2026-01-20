from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from .models import TabelaFrete, TabelaTaxa

class TabelaFreteListView(ListView):
    model = TabelaFrete
    template_name = 'canais_vendas/tabela_frete_list.html'
    context_object_name = 'tabelas'

class TabelaFreteDetailView(DetailView):
    model = TabelaFrete
    template_name = 'canais_vendas/tabela_frete_detail.html'
    context_object_name = 'tabela'

class TabelaFreteCreateView(CreateView):
    model = TabelaFrete
    template_name = 'canais_vendas/tabela_frete_form.html'
    fields = ['nome', 'tipo', 'descricao', 'ativo', 'suporta_nota_vendedor']
    success_url = reverse_lazy('tabela_frete_list')

class TabelaFreteUpdateView(UpdateView):
    model = TabelaFrete
    template_name = 'canais_vendas/tabela_frete_form.html'
    fields = ['nome', 'tipo', 'descricao', 'ativo', 'suporta_nota_vendedor']
    def get_success_url(self):
        return reverse('tabela_frete_detail', kwargs={'pk': self.object.pk})

class TabelaFreteDeleteView(DeleteView):
    model = TabelaFrete
    template_name = 'canais_vendas/tabela_frete_confirm_delete.html'
    success_url = reverse_lazy('tabela_frete_list')