import React, { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { 
  CheckCircle2, 
  Download, 
  RotateCcw, 
  FileSpreadsheet,
  FileText,
  Calendar,
  Building,
  Pencil,
  Check,
  X
} from 'lucide-react';

/**
 * Componente especializado para Extrato de Convênio (Movimentação Financeira)
 * Replica EXATAMENTE o formato da planilha GECOV
 */
export default function ConvenioResultSection({ data, onExport, onNewUpload, isExporting }) {
  // Formata valor monetário
  const formatCurrency = (value) => {
    // 0,00 deve aparecer explicitamente
    if (value === null || value === undefined) return '-';
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(Number(value) || 0);
  };

  const formatPlain = (value) => {
    if (value === null || value === undefined) return '-';
    const s = String(value);
    return s.length ? s : '-';
  };

  const parsePtBrNumber = (raw) => {
    if (raw === null || raw === undefined) return null;
    const s = String(raw)
      .replace(/[R$\s]/g, '')
      .replace(/\./g, '')
      .replace(',', '.')
      .trim();
    if (!s) return 0;
    const n = Number(s);
    return Number.isFinite(n) ? n : null;
  };

  // Pega os dados do convênio (primeiro item)
  const convenioData = data && data.length > 0 ? data[0] : null;
  
  // Aceita se for EXTRATO_CONVENIO_MOVIMENTACAO OU se tiver movimentacoes
  if (!convenioData) {
    return <div className="text-center text-gray-500">Nenhum dado para exibir</div>;
  }
  
  if (!convenioData.movimentacoes && convenioData.tipo_documento !== 'EXTRATO_CONVENIO_MOVIMENTACAO') {
    return <div className="text-center text-gray-500">Formato de documento não suportado</div>;
  }

  const { cabecalho = {}, movimentacoes = [], totais = {} } = convenioData;
  const documentosFiscais = convenioData?.documentos_fiscais || null;

  // Estado editável da tabela (para permitir edição com lápis)
  const [rows, setRows] = useState([]);
  const [editing, setEditing] = useState(null); // { rowIndex, field, value }

  // Estado editável das tabelas fiscais (3 tabelas abaixo)
  const [fiscais, setFiscais] = useState({
    contrato_empresa: [],
    previsao_pt: [],
    proporcionalidade: [],
    paginas_origem: [],
    inss_paginas_origem: [],
  });
  const [editingFiscal, setEditingFiscal] = useState(null); // { table, rowIndex, field, value }

  useEffect(() => {
    setRows(Array.isArray(movimentacoes) ? movimentacoes.map(m => ({ ...m })) : []);
    setEditing(null);
  }, [movimentacoes]);

  useEffect(() => {
    const df = documentosFiscais || {};
    setFiscais({
      contrato_empresa: Array.isArray(df.contrato_empresa) ? df.contrato_empresa.map(r => ({ ...r })) : [],
      previsao_pt: Array.isArray(df.previsao_pt) ? df.previsao_pt.map(r => ({ ...r })) : [],
      proporcionalidade: Array.isArray(df.proporcionalidade) ? df.proporcionalidade.map(r => ({ ...r })) : [],
      paginas_origem: Array.isArray(df.paginas_origem) ? df.paginas_origem : [],
      inss_paginas_origem: Array.isArray(df.inss_paginas_origem) ? df.inss_paginas_origem : [],
    });
    setEditingFiscal(null);
  }, [documentosFiscais]);

  const totalsComputed = useMemo(() => {
    const base = {
      total_entrada: 0,
      total_saida: 0,
      total_aplicacao: 0,
      total_resgate: 0,
      total_rendimentos: 0,
      total_tarifa_paga: 0,
      total_tarifa_devolvida: 0,
    };

    // Não somar linhas que são "total por página" (para não duplicar)
    const filtered = rows.filter(r => !r?.is_total_pagina);

    for (const r of filtered) {
      base.total_entrada += Number(r.entrada) || 0;
      base.total_saida += Number(r.saida) || 0;
      base.total_aplicacao += Number(r.aplicacao) || 0;
      base.total_resgate += Number(r.resgate) || 0;
      base.total_rendimentos += Number(r.rendimentos) || 0;
      base.total_tarifa_paga += Number(r.tarifa_paga) || 0;
      base.total_tarifa_devolvida += Number(r.tarifa_devolvida) || 0;
    }

    return {
      ...base,
      saldo_final: base.total_entrada - base.total_saida,
    };
  }, [rows]);

  const totaisToShow = totalsComputed || totais;

  const startEdit = (rowIndex, field) => {
    const current = rows?.[rowIndex]?.[field];
    setEditing({
      rowIndex,
      field,
      value: current === null || current === undefined ? '' : String(current).replace('.', ','),
    });
  };

  const cancelEdit = () => setEditing(null);

  const commitEdit = () => {
    if (!editing) return;
    const { rowIndex, field, value } = editing;
    const parsed = parsePtBrNumber(value);
    setRows(prev => {
      const next = [...prev];
      next[rowIndex] = { ...next[rowIndex], [field]: parsed === null ? next[rowIndex][field] : parsed };
      return next;
    });
    setEditing(null);
  };

  const fiscalNumericFields = new Set([
    // contrato_empresa
    'valor_bruto', 'inss', 'ir', 'iss', 'liquido',
    // previsao_pt
    'previsao_pt', 'repassado', 'executado', 'saldo_repasse', 'rendimento', 'saldo',
    // proporcionalidade
    'saldo', 'rend_nao_aplic', 'rend_tarifa', 'nota_tecnica', 'rend_nota_tec', 'atraso_dev',
    'total', 'saldo_devolvido', 'dev_maior_menor',
  ]);

  const startEditFiscal = (table, rowIndex, field) => {
    const current = fiscais?.[table]?.[rowIndex]?.[field];
    setEditingFiscal({
      table,
      rowIndex,
      field,
      value: current === null || current === undefined ? '' : String(current).replace('.', ','),
    });
  };

  const cancelEditFiscal = () => setEditingFiscal(null);

  const commitEditFiscal = () => {
    if (!editingFiscal) return;
    const { table, rowIndex, field, value } = editingFiscal;
    const parsed = fiscalNumericFields.has(field) ? parsePtBrNumber(value) : String(value);

    setFiscais(prev => {
      const next = { ...prev };
      const rowsTable = Array.isArray(next[table]) ? [...next[table]] : [];
      const oldRow = rowsTable[rowIndex] || {};
      rowsTable[rowIndex] = { ...oldRow, [field]: parsed === null ? oldRow[field] : parsed };
      next[table] = rowsTable;
      return next;
    });

    setEditingFiscal(null);
  };

  const renderFiscalCell = (table, row, rowIndex, field, opts = {}) => {
    const { alignRight = false, money = false, readOnly = false } = opts;
    const isEditing = editingFiscal?.table === table && editingFiscal?.rowIndex === rowIndex && editingFiscal?.field === field;
    const val = row?.[field];

    if (readOnly) {
      return (
        <div className={`flex items-center ${alignRight ? 'justify-end' : 'justify-start'} gap-2`}>
          <span className={`text-xs ${alignRight ? 'font-mono' : ''}`}>
            {money ? formatCurrency(val) : formatPlain(val)}
          </span>
        </div>
      );
    }

    if (isEditing) {
      return (
        <div className={`flex items-center ${alignRight ? 'justify-end' : 'justify-start'} gap-2`}>
          <input
            className="w-28 px-2 py-1 text-xs font-mono border rounded-md bg-white"
            value={editingFiscal.value}
            onChange={(e) => setEditingFiscal({ ...editingFiscal, value: e.target.value })}
            onKeyDown={(e) => {
              if (e.key === 'Enter') commitEditFiscal();
              if (e.key === 'Escape') cancelEditFiscal();
            }}
            autoFocus
          />
          <button className="p-1 text-green-700 hover:bg-green-50 rounded" onClick={commitEditFiscal} title="Salvar">
            <Check className="w-4 h-4" />
          </button>
          <button className="p-1 text-gray-600 hover:bg-gray-100 rounded" onClick={cancelEditFiscal} title="Cancelar">
            <X className="w-4 h-4" />
          </button>
        </div>
      );
    }

    return (
      <div className={`flex items-center ${alignRight ? 'justify-end' : 'justify-start'} gap-2`}>
        <span className={`text-xs ${alignRight ? 'font-mono' : ''}`}>
          {money ? formatCurrency(val) : formatPlain(val)}
        </span>
        <button
          className="p-1 text-gray-500 hover:text-gray-800 hover:bg-gray-100 rounded"
          onClick={() => startEditFiscal(table, rowIndex, field)}
          title="Editar"
        >
          <Pencil className="w-3.5 h-3.5" />
        </button>
      </div>
    );
  };

  const contratoTotals = useMemo(() => {
    const base = { valor_bruto: 0, inss: 0, ir: 0, iss: 0, liquido_doc: 0, liquido_calc: 0 };
    const rowsContrato = fiscais?.contrato_empresa || [];
    const filtered = rowsContrato.filter(r => !(r?.is_total) && (r?.nf || '') !== 'TOTAL');

    for (const r of filtered) {
      base.valor_bruto += Number(r.valor_bruto) || 0;
      base.inss += Number(r.inss) || 0;
      base.ir += Number(r.ir) || 0;
      base.iss += Number(r.iss) || 0;
      base.liquido_doc += Number(r.liquido) || 0;

      if (r.valor_bruto !== null && r.valor_bruto !== undefined) {
        base.liquido_calc += (Number(r.valor_bruto) || 0) - (Number(r.inss) || 0) - (Number(r.ir) || 0) - (Number(r.iss) || 0);
      }
    }

    return base;
  }, [fiscais]);

  const previsaoTotals = useMemo(() => {
    const base = { previsao_pt: 0, repassado: 0, executado: 0, saldo_repasse: 0, rendimento: 0, saldo: 0 };
    const rowsPrev = fiscais?.previsao_pt || [];
    const filtered = rowsPrev.filter(r => (r?.parte || '') !== 'TOTAL');

    for (const r of filtered) {
      base.previsao_pt += Number(r.previsao_pt) || 0;
      base.repassado += Number(r.repassado) || 0;
      base.executado += Number(r.executado) || 0;
      base.saldo_repasse += Number(r.saldo_repasse) || 0;
      base.rendimento += Number(r.rendimento) || 0;
      base.saldo += Number(r.saldo) || 0;
    }
    return base;
  }, [fiscais]);

  const propTotals = useMemo(() => {
    const base = {
      saldo: 0, rend_nao_aplic: 0, rend_tarifa: 0, nota_tecnica: 0, rend_nota_tec: 0, atraso_dev: 0,
      total: 0, saldo_devolvido: 0, dev_maior_menor: 0,
    };
    const rowsProp = fiscais?.proporcionalidade || [];
    const filtered = rowsProp.filter(r => (r?.parte || '') !== 'TOTAL');

    for (const r of filtered) {
      base.saldo += Number(r.saldo) || 0;
      base.rend_nao_aplic += Number(r.rend_nao_aplic) || 0;
      base.rend_tarifa += Number(r.rend_tarifa) || 0;
      base.nota_tecnica += Number(r.nota_tecnica) || 0;
      base.rend_nota_tec += Number(r.rend_nota_tec) || 0;
      base.atraso_dev += Number(r.atraso_dev) || 0;
      base.total += Number(r.total) || 0;
      base.saldo_devolvido += Number(r.saldo_devolvido) || 0;
      base.dev_maior_menor += Number(r.dev_maior_menor) || 0;
    }
    return base;
  }, [fiscais]);

  const renderMoneyCell = (mov, index, field, className = '') => {
    const isEditing = editing?.rowIndex === index && editing?.field === field;
    const val = mov?.[field];

    if (isEditing) {
      return (
        <div className={`flex items-center justify-end gap-2 ${className}`}>
          <input
            className="w-28 px-2 py-1 text-xs font-mono border rounded-md bg-white"
            value={editing.value}
            onChange={(e) => setEditing({ ...editing, value: e.target.value })}
            onKeyDown={(e) => {
              if (e.key === 'Enter') commitEdit();
              if (e.key === 'Escape') cancelEdit();
            }}
            autoFocus
          />
          <button className="p-1 text-green-700 hover:bg-green-50 rounded" onClick={commitEdit} title="Salvar">
            <Check className="w-4 h-4" />
          </button>
          <button className="p-1 text-gray-600 hover:bg-gray-100 rounded" onClick={cancelEdit} title="Cancelar">
            <X className="w-4 h-4" />
          </button>
        </div>
      );
    }

    return (
      <div className={`flex items-center justify-end gap-2 ${className}`}>
        <span className="font-mono text-xs">{formatCurrency(val)}</span>
        <button
          className="p-1 text-gray-500 hover:text-gray-800 hover:bg-gray-100 rounded"
          onClick={() => startEdit(index, field)}
          title="Editar"
        >
          <Pencil className="w-3.5 h-3.5" />
        </button>
      </div>
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="w-full max-w-[95vw] mx-auto"
    >
      {/* Cabeçalho de Sucesso */}
      <div className="text-center mb-8">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: "spring", stiffness: 200, damping: 15 }}
          className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6"
        >
          <CheckCircle2 className="w-10 h-10 text-green-600" />
        </motion.div>
        
        <h2 className="text-2xl font-bold text-gray-900 mb-1">
          CONCILIAÇÃO FINANCEIRA - GECOV
        </h2>
        <p className="text-lg font-semibold text-gray-700 mb-4">
          MOVIMENTAÇÃO FINANCEIRA
        </p>
      </div>

      {/* Card Principal */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden mb-6"
      >
        {/* Cabeçalho do Convênio */}
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 px-6 py-4 border-b border-gray-200">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <div className="text-xs font-semibold text-gray-600 mb-1 flex items-center gap-1">
                <FileText className="w-3 h-3" />
                Convênio
              </div>
              <div className="font-bold text-gray-900">{cabecalho?.convenio || 'N/A'}</div>
            </div>
            <div>
              <div className="text-xs font-semibold text-gray-600 mb-1 flex items-center gap-1">
                <Building className="w-3 h-3" />
                Convenente
              </div>
              <div className="font-bold text-gray-900">{cabecalho?.convenente || 'N/A'}</div>
            </div>
            <div>
              <div className="text-xs font-semibold text-gray-600 mb-1 flex items-center gap-1">
                <Calendar className="w-3 h-3" />
                Vigência
              </div>
              <div className="font-bold text-gray-900">{cabecalho?.vigencia || 'N/A'}</div>
            </div>
            <div>
              <div className="text-xs font-semibold text-gray-600 mb-1">CC</div>
              <div className="font-bold text-gray-900 font-mono">{cabecalho?.conta_corrente || 'N/A'}</div>
            </div>
          </div>
        </div>

        {/* Tabela de Movimentações */}
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-100 border-b-2 border-gray-300">
                <th className="px-3 py-3 text-left font-bold text-gray-700 whitespace-nowrap">Data</th>
                <th className="px-3 py-3 text-left font-bold text-gray-700 whitespace-nowrap">Item</th>
                <th className="px-3 py-3 text-right font-bold text-gray-700 whitespace-nowrap">Entrada</th>
                <th className="px-3 py-3 text-right font-bold text-gray-700 whitespace-nowrap">Saída</th>
                <th className="px-3 py-3 text-right font-bold text-gray-700 whitespace-nowrap">Saldo</th>
                <th className="px-3 py-3 text-right font-bold text-gray-700 whitespace-nowrap">Aplicação</th>
                <th className="px-3 py-3 text-right font-bold text-gray-700 whitespace-nowrap">Resgate</th>
                <th className="px-3 py-3 text-right font-bold text-gray-700 whitespace-nowrap">Rendimentos</th>
                <th className="px-3 py-3 text-right font-bold text-gray-700 whitespace-nowrap">Tarifa Paga</th>
                <th className="px-3 py-3 text-right font-bold text-gray-700 whitespace-nowrap">Tarifa Devolvida</th>
                <th className="px-3 py-3 text-right font-bold text-gray-700 whitespace-nowrap">Saldo de Tarifa</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {rows && rows.length > 0 ? (
                rows.map((mov, index) => (
                  <motion.tr
                    key={index}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: Math.min(0.05 * index, 1) }}
                    className={`hover:bg-blue-50 transition-colors ${index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}`}
                  >
                    <td className="px-3 py-2 font-mono text-xs text-gray-700">{mov.data || '-'}</td>
                    <td className="px-3 py-2 text-xs text-gray-700">{mov.item || '-'}</td>
                    <td className="px-3 py-2">
                      {renderMoneyCell(mov, index, 'entrada', `${mov.entrada > 0 ? 'text-green-700 font-semibold' : 'text-gray-600'}`)}
                    </td>
                    <td className="px-3 py-2">
                      {renderMoneyCell(mov, index, 'saida', `${mov.saida > 0 ? 'text-red-700 font-semibold' : 'text-gray-600'}`)}
                    </td>
                    <td className="px-3 py-2">
                      {renderMoneyCell(mov, index, 'saldo', `text-blue-700 font-semibold`)}
                    </td>
                    <td className="px-3 py-2">
                      {renderMoneyCell(mov, index, 'aplicacao', `text-gray-700`)}
                    </td>
                    <td className="px-3 py-2">
                      {renderMoneyCell(mov, index, 'resgate', `text-gray-700`)}
                    </td>
                    <td className="px-3 py-2">
                      {renderMoneyCell(mov, index, 'rendimentos', `text-green-600`)}
                    </td>
                    <td className="px-3 py-2">
                      {renderMoneyCell(mov, index, 'tarifa_paga', `text-gray-700`)}
                    </td>
                    <td className="px-3 py-2">
                      {renderMoneyCell(mov, index, 'tarifa_devolvida', `text-gray-700`)}
                    </td>
                    <td className="px-3 py-2">
                      {renderMoneyCell(mov, index, 'saldo_tarifa', `text-gray-700`)}
                    </td>
                  </motion.tr>
                ))
              ) : (
                <tr>
                  <td colSpan={11} className="px-6 py-8 text-center text-gray-500">
                    Nenhuma movimentação encontrada
                  </td>
                </tr>
              )}
            </tbody>
            
            {/* Linha TOTAL */}
            {totaisToShow && (
              <tfoot>
                <tr className="bg-yellow-100 border-t-2 border-yellow-400">
                  <td className="px-3 py-3 font-bold text-gray-900 uppercase">TOTAL</td>
                  <td className="px-3 py-3"></td>
                  <td className="px-3 py-3 text-right font-bold text-green-700 text-base">
                    {formatCurrency(totaisToShow.total_entrada)}
                  </td>
                  <td className="px-3 py-3 text-right font-bold text-red-700 text-base">
                    {formatCurrency(totaisToShow.total_saida)}
                  </td>
                  <td className="px-3 py-3 text-right font-bold text-blue-800 text-base">
                    {formatCurrency(totaisToShow.saldo_final)}
                  </td>
                  <td className="px-3 py-3 text-right font-bold text-gray-800">
                    {formatCurrency(totaisToShow.total_aplicacao)}
                  </td>
                  <td className="px-3 py-3 text-right font-bold text-gray-800">
                    {formatCurrency(totaisToShow.total_resgate)}
                  </td>
                  <td className="px-3 py-3 text-right font-bold text-green-700">
                    {formatCurrency(totaisToShow.total_rendimentos)}
                  </td>
                  <td className="px-3 py-3 text-right font-bold text-gray-800">
                    {formatCurrency(totaisToShow.total_tarifa_paga)}
                  </td>
                  <td className="px-3 py-3 text-right font-bold text-gray-800">
                    {formatCurrency(totaisToShow.total_tarifa_devolvida)}
                  </td>
                  <td className="px-3 py-3"></td>
                </tr>
              </tfoot>
            )}
          </table>
        </div>
      </motion.div>

      {/* ===================== DOCUMENTOS FISCAIS (3 TABELAS) ===================== */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.25 }}
        className="bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden mb-6"
      >
        <div className="bg-gradient-to-r from-slate-50 to-white px-6 py-4 border-b border-gray-200">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
            <div className="font-bold text-gray-900">DOCUMENTOS FISCAIS</div>
            <div className="text-xs text-gray-600">
              Páginas com INSS: <span className="font-mono font-semibold">{(fiscais?.inss_paginas_origem || []).join(', ') || '-'}</span>
            </div>
          </div>
          <div className="mt-1 text-xs text-gray-500">
            Páginas detectadas: <span className="font-mono">{(fiscais?.paginas_origem || []).join(', ') || '-'}</span>
          </div>
        </div>

        {/* CONTRATO EMPRESA */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="font-semibold text-gray-900 mb-3">Contrato Empresa (Notas Fiscais)</div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-100 border-b border-gray-200">
                  <th className="px-3 py-2 text-left text-xs font-bold text-gray-700 whitespace-nowrap">NF</th>
                  <th className="px-3 py-2 text-left text-xs font-bold text-gray-700 whitespace-nowrap">Data Emissão</th>
                  <th className="px-3 py-2 text-right text-xs font-bold text-gray-700 whitespace-nowrap">Valor Bruto</th>
                  <th className="px-3 py-2 text-right text-xs font-bold text-gray-700 whitespace-nowrap">INSS</th>
                  <th className="px-3 py-2 text-right text-xs font-bold text-gray-700 whitespace-nowrap">IR</th>
                  <th className="px-3 py-2 text-right text-xs font-bold text-gray-700 whitespace-nowrap">ISS</th>
                  <th className="px-3 py-2 text-right text-xs font-bold text-gray-700 whitespace-nowrap">Líquido (doc)</th>
                  <th className="px-3 py-2 text-right text-xs font-bold text-gray-700 whitespace-nowrap">Líquido (calc)</th>
                  <th className="px-3 py-2 text-left text-xs font-bold text-gray-700 whitespace-nowrap">Data PG</th>
                  <th className="px-3 py-2 text-left text-xs font-bold text-gray-700 whitespace-nowrap">Página</th>
                  <th className="px-3 py-2 text-left text-xs font-bold text-gray-700 whitespace-nowrap">INSS FLS</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {(fiscais?.contrato_empresa || []).length ? (
                  (fiscais.contrato_empresa || []).map((r, idx) => {
                    const liquidoCalc = (r?.valor_bruto === null || r?.valor_bruto === undefined)
                      ? null
                      : (Number(r.valor_bruto) || 0) - (Number(r.inss) || 0) - (Number(r.ir) || 0) - (Number(r.iss) || 0);

                    const isTotal = r?.is_total || r?.nf === 'TOTAL';

                    return (
                      <tr key={idx} className={`${idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'} ${isTotal ? 'bg-yellow-50' : ''}`}>
                        <td className="px-3 py-2">{renderFiscalCell('contrato_empresa', r, idx, 'nf')}</td>
                        <td className="px-3 py-2">{renderFiscalCell('contrato_empresa', r, idx, 'data_emissao')}</td>
                        <td className="px-3 py-2">{renderFiscalCell('contrato_empresa', r, idx, 'valor_bruto', { alignRight: true, money: true })}</td>
                        <td className="px-3 py-2">{renderFiscalCell('contrato_empresa', r, idx, 'inss', { alignRight: true, money: true })}</td>
                        <td className="px-3 py-2">{renderFiscalCell('contrato_empresa', r, idx, 'ir', { alignRight: true, money: true })}</td>
                        <td className="px-3 py-2">{renderFiscalCell('contrato_empresa', r, idx, 'iss', { alignRight: true, money: true })}</td>
                        <td className="px-3 py-2">{renderFiscalCell('contrato_empresa', r, idx, 'liquido', { alignRight: true, money: true })}</td>
                        <td className="px-3 py-2">
                          <div className="flex items-center justify-end gap-2">
                            <span className="font-mono text-xs">{formatCurrency(liquidoCalc)}</span>
                          </div>
                        </td>
                        <td className="px-3 py-2">{renderFiscalCell('contrato_empresa', r, idx, 'data_pg')}</td>
                        <td className="px-3 py-2">
                          <div className="font-mono text-xs">{(r?.paginas_origem || []).join(', ') || '-'}</div>
                        </td>
                        <td className="px-3 py-2">{renderFiscalCell('contrato_empresa', r, idx, 'inss_fls')}</td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={11} className="px-6 py-6 text-center text-gray-500 text-sm">Nenhuma linha encontrada</td>
                  </tr>
                )}
              </tbody>
              <tfoot>
                <tr className="bg-yellow-100 border-t-2 border-yellow-400">
                  <td className="px-3 py-3 font-bold text-gray-900 uppercase">TOTAL</td>
                  <td className="px-3 py-3"></td>
                  <td className="px-3 py-3 text-right font-bold text-gray-900">{formatCurrency(contratoTotals.valor_bruto)}</td>
                  <td className="px-3 py-3 text-right font-bold text-gray-900">{formatCurrency(contratoTotals.inss)}</td>
                  <td className="px-3 py-3 text-right font-bold text-gray-900">{formatCurrency(contratoTotals.ir)}</td>
                  <td className="px-3 py-3 text-right font-bold text-gray-900">{formatCurrency(contratoTotals.iss)}</td>
                  <td className="px-3 py-3 text-right font-bold text-gray-900">{formatCurrency(contratoTotals.liquido_doc)}</td>
                  <td className="px-3 py-3 text-right font-bold text-gray-900">{formatCurrency(contratoTotals.liquido_calc)}</td>
                  <td className="px-3 py-3"></td>
                  <td className="px-3 py-3"></td>
                  <td className="px-3 py-3"></td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>

        {/* PREVISÃO PT */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="font-semibold text-gray-900 mb-3">Previsão PT</div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-100 border-b border-gray-200">
                  <th className="px-3 py-2 text-left text-xs font-bold text-gray-700 whitespace-nowrap">Parte</th>
                  <th className="px-3 py-2 text-right text-xs font-bold text-gray-700 whitespace-nowrap">Previsão PT</th>
                  <th className="px-3 py-2 text-left text-xs font-bold text-gray-700 whitespace-nowrap">%</th>
                  <th className="px-3 py-2 text-right text-xs font-bold text-gray-700 whitespace-nowrap">Repassado</th>
                  <th className="px-3 py-2 text-right text-xs font-bold text-gray-700 whitespace-nowrap">Executado</th>
                  <th className="px-3 py-2 text-right text-xs font-bold text-gray-700 whitespace-nowrap">Saldo Repasse</th>
                  <th className="px-3 py-2 text-right text-xs font-bold text-gray-700 whitespace-nowrap">Rendimento</th>
                  <th className="px-3 py-2 text-right text-xs font-bold text-gray-700 whitespace-nowrap">Saldo</th>
                  <th className="px-3 py-2 text-left text-xs font-bold text-gray-700 whitespace-nowrap">Página</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {(fiscais?.previsao_pt || []).length ? (
                  (fiscais.previsao_pt || []).map((r, idx) => (
                    <tr key={idx} className={`${idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}`}>
                      <td className="px-3 py-2">{renderFiscalCell('previsao_pt', r, idx, 'parte')}</td>
                      <td className="px-3 py-2">{renderFiscalCell('previsao_pt', r, idx, 'previsao_pt', { alignRight: true, money: true })}</td>
                      <td className="px-3 py-2">{renderFiscalCell('previsao_pt', r, idx, 'percentual')}</td>
                      <td className="px-3 py-2">{renderFiscalCell('previsao_pt', r, idx, 'repassado', { alignRight: true, money: true })}</td>
                      <td className="px-3 py-2">{renderFiscalCell('previsao_pt', r, idx, 'executado', { alignRight: true, money: true })}</td>
                      <td className="px-3 py-2">{renderFiscalCell('previsao_pt', r, idx, 'saldo_repasse', { alignRight: true, money: true })}</td>
                      <td className="px-3 py-2">{renderFiscalCell('previsao_pt', r, idx, 'rendimento', { alignRight: true, money: true })}</td>
                      <td className="px-3 py-2">{renderFiscalCell('previsao_pt', r, idx, 'saldo', { alignRight: true, money: true })}</td>
                      <td className="px-3 py-2">
                        <div className="font-mono text-xs">{(r?.paginas_origem || []).join(', ') || '-'}</div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={9} className="px-6 py-6 text-center text-gray-500 text-sm">Nenhuma linha encontrada</td>
                  </tr>
                )}
              </tbody>
              <tfoot>
                <tr className="bg-yellow-100 border-t-2 border-yellow-400">
                  <td className="px-3 py-3 font-bold text-gray-900 uppercase">TOTAL</td>
                  <td className="px-3 py-3 text-right font-bold text-gray-900">{formatCurrency(previsaoTotals.previsao_pt)}</td>
                  <td className="px-3 py-3"></td>
                  <td className="px-3 py-3 text-right font-bold text-gray-900">{formatCurrency(previsaoTotals.repassado)}</td>
                  <td className="px-3 py-3 text-right font-bold text-gray-900">{formatCurrency(previsaoTotals.executado)}</td>
                  <td className="px-3 py-3 text-right font-bold text-gray-900">{formatCurrency(previsaoTotals.saldo_repasse)}</td>
                  <td className="px-3 py-3 text-right font-bold text-gray-900">{formatCurrency(previsaoTotals.rendimento)}</td>
                  <td className="px-3 py-3 text-right font-bold text-gray-900">{formatCurrency(previsaoTotals.saldo)}</td>
                  <td className="px-3 py-3"></td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>

        {/* PROPORCIONALIDADE */}
        <div className="px-6 py-4">
          <div className="font-semibold text-gray-900 mb-3">Proporcionalidade</div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-100 border-b border-gray-200">
                  <th className="px-3 py-2 text-left text-xs font-bold text-gray-700 whitespace-nowrap">Parte</th>
                  <th className="px-3 py-2 text-right text-xs font-bold text-gray-700 whitespace-nowrap">Saldo</th>
                  <th className="px-3 py-2 text-right text-xs font-bold text-gray-700 whitespace-nowrap">Rend. Não Aplic</th>
                  <th className="px-3 py-2 text-right text-xs font-bold text-gray-700 whitespace-nowrap">Rend. Tarifa</th>
                  <th className="px-3 py-2 text-right text-xs font-bold text-gray-700 whitespace-nowrap">Nota Técnica</th>
                  <th className="px-3 py-2 text-right text-xs font-bold text-gray-700 whitespace-nowrap">Rend. Nota Tec</th>
                  <th className="px-3 py-2 text-right text-xs font-bold text-gray-700 whitespace-nowrap">Atraso Dev.</th>
                  <th className="px-3 py-2 text-right text-xs font-bold text-gray-700 whitespace-nowrap">Total</th>
                  <th className="px-3 py-2 text-right text-xs font-bold text-gray-700 whitespace-nowrap">Saldo Devolvido</th>
                  <th className="px-3 py-2 text-right text-xs font-bold text-gray-700 whitespace-nowrap">Dev. Maior/Menor</th>
                  <th className="px-3 py-2 text-left text-xs font-bold text-gray-700 whitespace-nowrap">Página</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {(fiscais?.proporcionalidade || []).length ? (
                  (fiscais.proporcionalidade || []).map((r, idx) => (
                    <tr key={idx} className={`${idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}`}>
                      <td className="px-3 py-2">{renderFiscalCell('proporcionalidade', r, idx, 'parte')}</td>
                      <td className="px-3 py-2">{renderFiscalCell('proporcionalidade', r, idx, 'saldo', { alignRight: true, money: true })}</td>
                      <td className="px-3 py-2">{renderFiscalCell('proporcionalidade', r, idx, 'rend_nao_aplic', { alignRight: true, money: true })}</td>
                      <td className="px-3 py-2">{renderFiscalCell('proporcionalidade', r, idx, 'rend_tarifa', { alignRight: true, money: true })}</td>
                      <td className="px-3 py-2">{renderFiscalCell('proporcionalidade', r, idx, 'nota_tecnica', { alignRight: true, money: true })}</td>
                      <td className="px-3 py-2">{renderFiscalCell('proporcionalidade', r, idx, 'rend_nota_tec', { alignRight: true, money: true })}</td>
                      <td className="px-3 py-2">{renderFiscalCell('proporcionalidade', r, idx, 'atraso_dev', { alignRight: true, money: true })}</td>
                      <td className="px-3 py-2">{renderFiscalCell('proporcionalidade', r, idx, 'total', { alignRight: true, money: true })}</td>
                      <td className="px-3 py-2">{renderFiscalCell('proporcionalidade', r, idx, 'saldo_devolvido', { alignRight: true, money: true })}</td>
                      <td className="px-3 py-2">{renderFiscalCell('proporcionalidade', r, idx, 'dev_maior_menor', { alignRight: true, money: true })}</td>
                      <td className="px-3 py-2">
                        <div className="font-mono text-xs">{(r?.paginas_origem || []).join(', ') || '-'}</div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={11} className="px-6 py-6 text-center text-gray-500 text-sm">Nenhuma linha encontrada</td>
                  </tr>
                )}
              </tbody>
              <tfoot>
                <tr className="bg-yellow-100 border-t-2 border-yellow-400">
                  <td className="px-3 py-3 font-bold text-gray-900 uppercase">TOTAL</td>
                  <td className="px-3 py-3 text-right font-bold text-gray-900">{formatCurrency(propTotals.saldo)}</td>
                  <td className="px-3 py-3 text-right font-bold text-gray-900">{formatCurrency(propTotals.rend_nao_aplic)}</td>
                  <td className="px-3 py-3 text-right font-bold text-gray-900">{formatCurrency(propTotals.rend_tarifa)}</td>
                  <td className="px-3 py-3 text-right font-bold text-gray-900">{formatCurrency(propTotals.nota_tecnica)}</td>
                  <td className="px-3 py-3 text-right font-bold text-gray-900">{formatCurrency(propTotals.rend_nota_tec)}</td>
                  <td className="px-3 py-3 text-right font-bold text-gray-900">{formatCurrency(propTotals.atraso_dev)}</td>
                  <td className="px-3 py-3 text-right font-bold text-gray-900">{formatCurrency(propTotals.total)}</td>
                  <td className="px-3 py-3 text-right font-bold text-gray-900">{formatCurrency(propTotals.saldo_devolvido)}</td>
                  <td className="px-3 py-3 text-right font-bold text-gray-900">{formatCurrency(propTotals.dev_maior_menor)}</td>
                  <td className="px-3 py-3"></td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      </motion.div>

      {/* Botões de Ação */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="flex flex-col sm:flex-row gap-4 justify-center"
      >
        <motion.button
          onClick={onExport}
          disabled={isExporting || !rows?.length}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className={`
            flex items-center justify-center gap-3 px-8 py-4 rounded-xl font-semibold
            transition-all duration-300 shadow-lg
            ${rows?.length && !isExporting
              ? 'bg-gradient-to-r from-green-600 to-green-700 text-white hover:shadow-green-200 hover:shadow-xl'
              : 'bg-gray-100 text-gray-400 cursor-not-allowed shadow-none'
            }
          `}
        >
          {isExporting ? (
            <>
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              >
                <Download className="w-5 h-5" />
              </motion.div>
              Exportando...
            </>
          ) : (
            <>
              <FileSpreadsheet className="w-5 h-5" />
              Exportar para Excel
            </>
          )}
        </motion.button>

        <motion.button
          onClick={onNewUpload}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="flex items-center justify-center gap-3 px-8 py-4 rounded-xl font-semibold bg-white border-2 border-gray-200 text-gray-700 hover:bg-gray-50 hover:border-gray-300 transition-all duration-300"
        >
          <RotateCcw className="w-5 h-5" />
          Novo Upload
        </motion.button>
      </motion.div>
    </motion.div>
  );
}
