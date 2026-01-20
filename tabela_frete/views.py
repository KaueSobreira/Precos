from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.forms import modelformset_factory
from .models import TabelaFrete, RegraFreteMatriz, RegraFreteSimples, DescontoNotaVendedor

# --- Tabela Frete ---

class RegrasMatrizBulkEditView(View):
    template_name = 'tabela_frete/regras_bulk_edit.html'

    def get(self, request, tabela_pk):
        tabela = get_object_or_404(TabelaFrete, pk=tabela_pk)
        RegraFormSet = modelformset_factory(
            RegraFreteMatriz,
            fields=['ordem', 'peso_inicio', 'peso_fim', 'preco_inicio', 'preco_fim', 'valor_frete', 'ativo'],
            extra=0,
            can_delete=True
        )
        formset = RegraFormSet(queryset=RegraFreteMatriz.objects.filter(tabela=tabela).order_by('ordem', 'peso_inicio'))
        return render(request, self.template_name, {'tabela': tabela, 'formset': formset})

    def post(self, request, tabela_pk):
        tabela = get_object_or_404(TabelaFrete, pk=tabela_pk)
        RegraFormSet = modelformset_factory(
            RegraFreteMatriz,
            fields=['ordem', 'peso_inicio', 'peso_fim', 'preco_inicio', 'preco_fim', 'valor_frete', 'ativo'],
            extra=0,
            can_delete=True
        )
        # É importante passar o queryset no POST também para garantir a integridade dos IDs
        formset = RegraFormSet(request.POST, queryset=RegraFreteMatriz.objects.filter(tabela=tabela).order_by('ordem', 'peso_inicio'))
        
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.tabela = tabela
                instance.save()
            for obj in formset.deleted_objects:
                obj.delete()
            messages.success(request, 'Regras atualizadas com sucesso!')
            return redirect('tabela_frete_detail', pk=tabela.pk)
        else:
            print("--- Formset Errors ---")
            print(formset.errors)
            print(formset.non_form_errors())
            messages.error(request, 'Erro ao salvar. Verifique os campos.')
        
        return render(request, self.template_name, {'tabela': tabela, 'formset': formset})

class TabelaFreteListView(ListView):
    model = TabelaFrete
    template_name = 'canais_vendas/tabela_frete_list.html'
    context_object_name = 'tabelas'

class TabelaFreteDetailView(DetailView):
    model = TabelaFrete
    template_name = 'canais_vendas/tabela_frete_detail.html'
    context_object_name = 'tabela'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object.tipo == 'matriz':
            context['regras'] = self.object.regras_matriz.all().order_by('ordem', 'peso_inicio')
        else:
            context['regras'] = self.object.regras_simples.all().order_by('inicio')
        
        context['descontos'] = self.object.descontos_nota.all().order_by('nota')
        return context

class TabelaFreteCreateView(CreateView):
    model = TabelaFrete
    template_name = 'canais_vendas/tabela_frete_form.html'
    fields = ['nome', 'tipo', 'descricao', 'ativo', 'suporta_nota_vendedor', 'adicionar_taxa_fixa', 'valor_taxa_fixa']
    success_url = reverse_lazy('tabela_frete_list')

class TabelaFreteUpdateView(UpdateView):
    model = TabelaFrete
    template_name = 'canais_vendas/tabela_frete_form.html'
    fields = ['nome', 'tipo', 'descricao', 'ativo', 'suporta_nota_vendedor', 'adicionar_taxa_fixa', 'valor_taxa_fixa']
    def get_success_url(self):
        return reverse('tabela_frete_detail', kwargs={'pk': self.object.pk})

class TabelaFreteDeleteView(DeleteView):
    model = TabelaFrete
    template_name = 'canais_vendas/tabela_frete_confirm_delete.html'
    success_url = reverse_lazy('tabela_frete_list')


# --- Regra Matriz ---

class RegraMatrizCreateView(CreateView):
    model = RegraFreteMatriz
    template_name = 'tabela_frete/regra_form.html'
    fields = ['ordem', 'peso_inicio', 'peso_fim', 'preco_inicio', 'preco_fim', 'valor_frete', 'ativo']

    def dispatch(self, request, *args, **kwargs):
        self.tabela = get_object_or_404(TabelaFrete, pk=kwargs['tabela_pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.tabela = self.tabela
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tabela'] = self.tabela
        context['titulo'] = "Nova Regra Matriz"
        return context

    def get_success_url(self):
        return reverse('tabela_frete_detail', kwargs={'pk': self.tabela.pk})

class RegraMatrizUpdateView(UpdateView):
    model = RegraFreteMatriz
    template_name = 'tabela_frete/regra_form.html'
    fields = ['ordem', 'peso_inicio', 'peso_fim', 'preco_inicio', 'preco_fim', 'valor_frete', 'ativo']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tabela'] = self.object.tabela
        context['titulo'] = "Editar Regra Matriz"
        return context

    def get_success_url(self):
        return reverse('tabela_frete_detail', kwargs={'pk': self.object.tabela.pk})

class RegraMatrizDeleteView(DeleteView):
    model = RegraFreteMatriz
    template_name = 'tabela_frete/regra_confirm_delete.html'
    
    def get_success_url(self):
        return reverse('tabela_frete_detail', kwargs={'pk': self.object.tabela.pk})


# --- Regra Simples ---

class RegraSimplesCreateView(CreateView):
    model = RegraFreteSimples
    template_name = 'tabela_frete/regra_simples_form.html'
    fields = ['inicio', 'fim', 'valor_frete', 'ativo']

    def dispatch(self, request, *args, **kwargs):
        self.tabela = get_object_or_404(TabelaFrete, pk=kwargs['tabela_pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.tabela = self.tabela
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tabela'] = self.tabela
        context['titulo'] = f"Nova Regra ({self.tabela.get_tipo_display()})"
        return context

    def get_success_url(self):
        return reverse('tabela_frete_detail', kwargs={'pk': self.tabela.pk})

class RegraSimplesUpdateView(UpdateView):
    model = RegraFreteSimples
    template_name = 'tabela_frete/regra_simples_form.html'
    fields = ['inicio', 'fim', 'valor_frete', 'ativo']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tabela'] = self.object.tabela
        context['titulo'] = "Editar Regra"
        return context

    def get_success_url(self):
        return reverse('tabela_frete_detail', kwargs={'pk': self.object.tabela.pk})

class RegraSimplesDeleteView(DeleteView):
    model = RegraFreteSimples
    template_name = 'tabela_frete/regra_confirm_delete.html'
    
    def get_success_url(self):
        return reverse('tabela_frete_detail', kwargs={'pk': self.object.tabela.pk})


# --- Desconto Nota ---

class DescontoCreateView(CreateView):
    model = DescontoNotaVendedor
    template_name = 'tabela_frete/desconto_form.html'
    fields = ['nota', 'percentual_desconto']

    def dispatch(self, request, *args, **kwargs):
        self.tabela = get_object_or_404(TabelaFrete, pk=kwargs['tabela_pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.tabela = self.tabela
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tabela'] = self.tabela
        return context

    def get_success_url(self):
        return reverse('tabela_frete_detail', kwargs={'pk': self.tabela.pk})

class DescontoUpdateView(UpdateView):
    model = DescontoNotaVendedor
    template_name = 'tabela_frete/desconto_form.html'
    fields = ['nota', 'percentual_desconto']

    def get_success_url(self):
        return reverse('tabela_frete_detail', kwargs={'pk': self.object.tabela.pk})

class DescontoDeleteView(DeleteView):
    model = DescontoNotaVendedor
    template_name = 'tabela_frete/regra_confirm_delete.html'
    
    def get_success_url(self):
        return reverse('tabela_frete_detail', kwargs={'pk': self.object.tabela.pk})
