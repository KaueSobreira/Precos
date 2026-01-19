from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.forms import modelformset_factory

from .models import CanalVenda, TabelaFrete, RegraFrete
from grupo_vendas.models import GrupoCanais


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
        'tipo_frete', 'frete_fixo', 'tabela_frete'
    ]
    success_url = reverse_lazy('canal_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grupos'] = GrupoCanais.objects.all()
        context['tabelas_frete'] = TabelaFrete.objects.filter(ativo=True)
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
        'tipo_frete', 'frete_fixo', 'tabela_frete'
    ]

    def get_success_url(self):
        return reverse('canal_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grupos'] = GrupoCanais.objects.all()
        context['tabelas_frete'] = TabelaFrete.objects.filter(ativo=True)
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


# Views de Tabelas de Frete
class TabelaFreteListView(ListView):
    model = TabelaFrete
    template_name = 'canais_vendas/tabela_frete_list.html'
    context_object_name = 'tabelas'

    def get_queryset(self):
        return TabelaFrete.objects.prefetch_related('regras', 'canais')


class TabelaFreteDetailView(DetailView):
    model = TabelaFrete
    template_name = 'canais_vendas/tabela_frete_detail.html'
    context_object_name = 'tabela'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['regras'] = self.object.regras.filter(ativo=True).order_by('ordem')
        context['canais'] = self.object.canais.filter(ativo=True)
        return context


class TabelaFreteCreateView(CreateView):
    model = TabelaFrete
    template_name = 'canais_vendas/tabela_frete_form.html'
    fields = ['nome', 'tipo', 'descricao', 'ativo']
    success_url = reverse_lazy('tabela_frete_list')

    def form_valid(self, form):
        messages.success(self.request, 'Tabela de frete criada com sucesso!')
        return super().form_valid(form)


class TabelaFreteUpdateView(UpdateView):
    model = TabelaFrete
    template_name = 'canais_vendas/tabela_frete_form.html'
    fields = ['nome', 'tipo', 'descricao', 'ativo']

    def get_success_url(self):
        return reverse('tabela_frete_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Tabela de frete atualizada com sucesso!')
        return super().form_valid(form)


class TabelaFreteDeleteView(DeleteView):
    model = TabelaFrete
    template_name = 'canais_vendas/tabela_frete_confirm_delete.html'
    success_url = reverse_lazy('tabela_frete_list')

    def form_valid(self, form):
        messages.success(self.request, 'Tabela de frete excluída com sucesso!')
        return super().form_valid(form)


def regras_frete_edit(request, tabela_pk):
    """Edição das regras de uma tabela de frete"""
    tabela = get_object_or_404(TabelaFrete, pk=tabela_pk)

    RegraFormSet = modelformset_factory(
        RegraFrete,
        fields=['ordem', 'tipo_condicao', 'operador', 'valor_limite', 'valor_frete', 'ativo'],
        extra=1,
        can_delete=True
    )

    if request.method == 'POST':
        formset = RegraFormSet(request.POST, queryset=tabela.regras.all())
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.tabela = tabela
                instance.save()
            for obj in formset.deleted_objects:
                obj.delete()
            messages.success(request, 'Regras de frete atualizadas com sucesso!')
            return redirect('tabela_frete_detail', pk=tabela.pk)
    else:
        formset = RegraFormSet(queryset=tabela.regras.all().order_by('ordem'))

    return render(request, 'canais_vendas/regras_frete_form.html', {
        'tabela': tabela,
        'formset': formset,
    })
