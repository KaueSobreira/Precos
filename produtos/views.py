from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.db.models import Count
from django.forms import modelformset_factory
from django.db import transaction
from decimal import Decimal

from django.db.models import Q

from .models import Produto, TituloProduto, ItemFichaTecnica, PrecoProdutoCanal, HistoricoPreco
from canais_vendas.models import CanalVenda
from grupo_vendas.models import GrupoCanais


def home(request):
    """Dashboard principal"""
    context = {
        'total_produtos': Produto.objects.filter(ativo=True).count(),
        'total_grupos': GrupoCanais.objects.count(),
        'total_canais': CanalVenda.objects.filter(ativo=True).count(),
        'total_precos': PrecoProdutoCanal.objects.filter(ativo=True).count(),
        'ultimos_produtos': Produto.objects.filter(ativo=True).order_by('-criado_em')[:5],
        'ultimos_historicos': HistoricoPreco.objects.order_by('-data_registro')[:10],
    }
    return render(request, 'produtos/home.html', context)


class ProdutoListView(ListView):
    model = Produto
    template_name = 'produtos/produto_list.html'
    context_object_name = 'produtos'
    paginate_by = 20

    def get_queryset(self):
        queryset = Produto.objects.all()
        search = self.request.GET.get('search')
        if search:
            # Pesquisa no produto principal e nos títulos alternativos
            queryset = queryset.filter(
                Q(sku__icontains=search) |
                Q(titulo__icontains=search) |
                Q(titulos__titulo__icontains=search)
            ).distinct()
        return queryset.order_by('-criado_em')


class ProdutoDetailView(DetailView):
    model = Produto
    template_name = 'produtos/produto_detail.html'
    context_object_name = 'produto'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['itens_ficha'] = self.object.itens_ficha.all()
        context['precos_canais'] = self.object.precos_canais.filter(ativo=True).select_related('canal', 'canal__grupo')
        context['titulos'] = self.object.titulos.filter(ativo=True)
        return context


class ProdutoCreateView(CreateView):
    model = Produto
    template_name = 'produtos/produto_form.html'
    fields = ['titulo', 'sku', 'ean', 'mlb', 'mlb_vinculado', 'largura', 'altura', 'profundidade', 'peso_fisico', 'desconto_estrategico', 'ativo']

    def get_success_url(self):
        # Redireciona para a ficha técnica após criar o produto
        return reverse('ficha_tecnica_edit', kwargs={'produto_pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Produto criado! Agora cadastre a ficha técnica para definir o custo.')
        return super().form_valid(form)


class ProdutoUpdateView(UpdateView):
    model = Produto
    template_name = 'produtos/produto_form.html'
    fields = ['titulo', 'sku', 'ean', 'mlb', 'mlb_vinculado', 'largura', 'altura', 'profundidade', 'peso_fisico', 'desconto_estrategico', 'ativo']

    def get_success_url(self):
        return reverse('produto_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Produto atualizado com sucesso!')
        return super().form_valid(form)


class ProdutoDeleteView(DeleteView):
    model = Produto
    template_name = 'produtos/produto_confirm_delete.html'
    success_url = reverse_lazy('produto_list')

    def form_valid(self, form):
        messages.success(self.request, 'Produto excluído com sucesso!')
        return super().form_valid(form)


def titulos_edit(request, produto_pk):
    """Edição dos títulos secundários de um produto"""
    produto = get_object_or_404(Produto, pk=produto_pk)

    TituloFormSet = modelformset_factory(
        TituloProduto,
        fields=['titulo', 'ativo'],
        extra=0,
        can_delete=True
    )

    if request.method == 'POST':
        formset = TituloFormSet(request.POST, queryset=produto.titulos.all(), prefix='titulo')

        if formset.is_valid():
            with transaction.atomic():
                instances = formset.save(commit=False)
                for instance in instances:
                    instance.produto = produto
                    instance.save()
                for obj in formset.deleted_objects:
                    obj.delete()

            messages.success(request, 'Títulos atualizados com sucesso!')
            return redirect('produto_detail', pk=produto.pk)
        else:
            for form in formset:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"Título - {field}: {error}")
            for error in formset.non_form_errors():
                messages.error(request, error)
    else:
        formset = TituloFormSet(queryset=produto.titulos.all(), prefix='titulo')

    return render(request, 'produtos/titulos_form.html', {
        'produto': produto,
        'formset': formset,
    })


def ficha_tecnica_edit(request, produto_pk):
    """Edição da ficha técnica de um produto"""
    produto = get_object_or_404(Produto, pk=produto_pk)

    FormSetBase = modelformset_factory(
        ItemFichaTecnica,
        fields=['codigo', 'descricao', 'unidade', 'quantidade', 'custo_unitario', 'multiplicador'],
        extra=0,
        can_delete=True
    )

    if request.method == 'POST':
        formset_mp = FormSetBase(request.POST, queryset=produto.itens_ficha.filter(tipo='MP'), prefix='mp')
        formset_terc = FormSetBase(request.POST, queryset=produto.itens_ficha.filter(tipo='TR'), prefix='terc')
        formset_emb = FormSetBase(request.POST, queryset=produto.itens_ficha.filter(tipo='EM'), prefix='emb')

        if formset_mp.is_valid() and formset_terc.is_valid() and formset_emb.is_valid():
            
            def salvar_formset(formset, tipo_item):
                instances = formset.save(commit=False)
                for instance in instances:
                    instance.produto = produto
                    instance.tipo = tipo_item
                    instance.save()
                for obj in formset.deleted_objects:
                    obj.delete()

            # Salvar em transação para garantir integridade
            with transaction.atomic():
                salvar_formset(formset_mp, 'MP')
                salvar_formset(formset_terc, 'TR')
                salvar_formset(formset_emb, 'EM')

            messages.success(request, 'Ficha técnica atualizada com sucesso!')
            return redirect('produto_detail', pk=produto.pk)
        else:
            # Consolidar erros e manter os formulários preenchidos
            all_errors = []
            for name, fs in [('Matéria Prima', formset_mp), ('Terceirizados', formset_terc), ('Embalagens', formset_emb)]:
                if not fs.is_valid():
                    for form in fs:
                        for field, errors in form.errors.items():
                            for error in errors:
                                all_errors.append(f"{name} - {field}: {error}")
                    for error in fs.non_form_errors():
                        all_errors.append(f"{name}: {error}")
            
            for err in all_errors:
                messages.error(request, err)
    else:
        formset_mp = FormSetBase(queryset=produto.itens_ficha.filter(tipo='MP'), prefix='mp')
        formset_terc = FormSetBase(queryset=produto.itens_ficha.filter(tipo='TR'), prefix='terc')
        formset_emb = FormSetBase(queryset=produto.itens_ficha.filter(tipo='EM'), prefix='emb')

    return render(request, 'produtos/ficha_tecnica_form.html', {
        'produto': produto,
        'formset_mp': formset_mp,
        'formset_terc': formset_terc,
        'formset_emb': formset_emb,
    })


class PrecoListView(ListView):
    model = PrecoProdutoCanal
    template_name = 'produtos/preco_list.html'
    context_object_name = 'precos'
    paginate_by = 50

    def get_queryset(self):
        queryset = PrecoProdutoCanal.objects.filter(ativo=True).select_related(
            'produto', 'canal', 'canal__grupo'
        )

        # Filtros
        produto = self.request.GET.get('produto')
        grupo = self.request.GET.get('grupo')
        canal = self.request.GET.get('canal')

        if produto:
            # Pesquisa no produto principal e nos títulos alternativos
            queryset = queryset.filter(
                Q(produto__sku__icontains=produto) |
                Q(produto__titulo__icontains=produto) |
                Q(produto__titulos__titulo__icontains=produto)
            ).distinct()
        if grupo:
            queryset = queryset.filter(canal__grupo_id=grupo)
        if canal:
            queryset = queryset.filter(canal_id=canal)

        return queryset.order_by('produto__sku', 'canal__grupo__nome', 'canal__nome')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grupos'] = GrupoCanais.objects.all()
        context['canais'] = CanalVenda.objects.filter(ativo=True)
        return context


def preco_edit(request, pk):
    """Edição de preço de um produto/canal"""
    preco = get_object_or_404(PrecoProdutoCanal, pk=pk)

    if request.method == 'POST':
        usar_auto = request.POST.get('usar_calculo_automatico') == 'on'
        preco.usar_calculo_automatico = usar_auto

        if not usar_auto:
            preco.preco_venda_manual = request.POST.get('preco_venda_manual') or None
            preco.preco_promocao_manual = request.POST.get('preco_promocao_manual') or None
            preco.preco_minimo_manual = request.POST.get('preco_minimo_manual') or None

        frete_especifico = request.POST.get('frete_especifico')
        preco.frete_especifico = frete_especifico if frete_especifico else None

        # Overrides de Parâmetros
        for field in ['imposto', 'operacao', 'lucro', 'promocao', 'minimo', 'ads', 'comissao']:
            val = request.POST.get(field)
            if val and val.strip():
                try:
                    # Remove % se houver e substitui vírgula
                    clean_val = val.replace('%', '').replace(',', '.')
                    setattr(preco, field, Decimal(clean_val))
                except Exception as e:
                    messages.warning(request, f"Valor inválido para {field.capitalize()}: {val}")
            else:
                setattr(preco, field, None)

        motivo = request.POST.get('motivo', '')

        try:
            preco.save(usuario=request.user if request.user.is_authenticated else None, motivo=motivo)
            messages.success(request, 'Preço atualizado com sucesso!')
            return redirect('preco_list')
        except Exception as e:
            messages.error(request, f'Erro ao salvar: {e}')

    return render(request, 'produtos/preco_edit.html', {'preco': preco})


def produto_precos(request, produto_pk):
    """Gerenciar preços de um produto em todos os canais"""
    produto = get_object_or_404(Produto, pk=produto_pk)
    canais = CanalVenda.objects.filter(ativo=True).select_related('grupo')

    if request.method == 'POST':
        canais_selecionados = request.POST.getlist('canais')

        for canal in canais:
            if str(canal.pk) in canais_selecionados:
                # Criar ou ativar preço
                preco, created = PrecoProdutoCanal.objects.get_or_create(
                    produto=produto,
                    canal=canal,
                    defaults={'ativo': True}
                )
                if not created and not preco.ativo:
                    preco.ativo = True
                    preco.save()
            else:
                # Desativar preço se existir
                PrecoProdutoCanal.objects.filter(
                    produto=produto, canal=canal
                ).update(ativo=False)

        messages.success(request, 'Preços atualizados com sucesso!')
        return redirect('produto_detail', pk=produto.pk)

    # Canais atualmente ativos para este produto
    canais_ativos = set(
        PrecoProdutoCanal.objects.filter(
            produto=produto, ativo=True
        ).values_list('canal_id', flat=True)
    )

    return render(request, 'produtos/produto_precos.html', {
        'produto': produto,
        'canais': canais,
        'canais_ativos': canais_ativos,
    })


class HistoricoListView(ListView):
    model = HistoricoPreco
    template_name = 'produtos/historico_list.html'
    context_object_name = 'historicos'
    paginate_by = 50

    def get_queryset(self):
        queryset = HistoricoPreco.objects.all()

        # Filtros
        produto = self.request.GET.get('produto')
        canal = self.request.GET.get('canal')
        data_inicio = self.request.GET.get('data_inicio')
        data_fim = self.request.GET.get('data_fim')

        if produto:
            queryset = queryset.filter(sku_produto__icontains=produto)
        if canal:
            queryset = queryset.filter(nome_canal__icontains=canal)
        if data_inicio:
            queryset = queryset.filter(data_registro__date__gte=data_inicio)
        if data_fim:
            queryset = queryset.filter(data_registro__date__lte=data_fim)

        return queryset.order_by('-data_registro')


class HistoricoDetailView(DetailView):
    model = HistoricoPreco
    template_name = 'produtos/historico_detail.html'
    context_object_name = 'historico'


class TabelaPrecosView(ListView):
    model = PrecoProdutoCanal
    template_name = 'produtos/tabela_precos.html'
    context_object_name = 'precos'
    paginate_by = 50

    def get_queryset(self):
        queryset = PrecoProdutoCanal.objects.filter(ativo=True).select_related(
            'produto', 'canal', 'canal__grupo'
        ).prefetch_related('produto__titulos')

        # Filtros
        search = self.request.GET.get('search')
        grupo = self.request.GET.get('grupo')
        canal = self.request.GET.get('canal')

        if grupo:
            queryset = queryset.filter(canal__grupo_id=grupo)
        if canal:
            queryset = queryset.filter(canal_id=canal)
        
        if search:
            # Filtra se houver match em qualquer título (Pai ou Filho) ou SKU
            queryset = queryset.filter(
                Q(produto__sku__icontains=search) |
                Q(produto__titulo__icontains=search) |
                Q(produto__titulos__titulo__icontains=search)
            ).distinct()

        return queryset.order_by('produto__sku', 'canal__grupo__nome', 'canal__nome')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Expandir os resultados da página atual
        page_precos = context['object_list']
        search = self.request.GET.get('search', '').lower()
        rows = []

        for preco in page_precos:
            # 1. Título Principal
            # Se não tem busca, OU se tem busca e bate com SKU ou Título Principal
            show_main = True
            if search:
                if not (search in preco.produto.sku.lower() or search in preco.produto.titulo.lower()):
                    show_main = False
            
            if show_main:
                rows.append({
                    'titulo': preco.produto.titulo,
                    'obj': preco,
                    'is_main': True
                })

            # 2. Títulos Secundários
            for titulo_sec in preco.produto.titulos.all():
                if not titulo_sec.ativo:
                    continue
                
                show_sec = True
                if search:
                    if search not in titulo_sec.titulo.lower():
                        show_sec = False
                
                if show_sec:
                    rows.append({
                        'titulo': titulo_sec.titulo,
                        'obj': preco,
                        'is_main': False
                    })
        
        context['rows'] = rows
        context['grupos'] = GrupoCanais.objects.all()
        context['canais'] = CanalVenda.objects.filter(ativo=True)
        return context
