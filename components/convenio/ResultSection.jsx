import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  CheckCircle2, 
  Download, 
  RotateCcw, 
  Building2, 
  MapPin, 
  CreditCard, 
  DollarSign,
  FileSpreadsheet,
  ChevronDown,
  ChevronUp,
  TrendingUp,
  Calendar,
  Wallet
} from 'lucide-react';

/**
 * Componente de Resultado Expandido
 * Suporta extrato bancário comum E extrato de investimento
 */
export default function ResultSection({ data, onExport, onNewUpload, isExporting }) {
  const [expandedRows, setExpandedRows] = useState({});

  // Formata valor monetário
  const formatCurrency = (value) => {
    if (value === null || value === undefined) return '-';
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  // Formata percentual
  const formatPercent = (value) => {
    if (value === null || value === undefined) return '-';
    return `${value.toFixed(4)}%`;
  };

  // Toggle expandir linha
  const toggleRow = (index) => {
    setExpandedRows(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  // Detecta se é extrato de investimento
  const isInvestmentExtract = (item) => {
    return item.tipo_documento === 'EXTRATO_INVESTIMENTO_FUNDO_PUBLICO' || 
           item.valores_principais !== undefined ||
           item.rentabilidade !== undefined;
  };

  // Calcula total (só para extratos comuns)
  const total = data?.reduce((sum, item) => {
    if (isInvestmentExtract(item)) {
      return sum + (item.valores_principais?.saldo_atual || 0);
    }
    return sum + (item.valor || 0);
  }, 0) || 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="w-full max-w-6xl mx-auto"
    >
      {/* Cabeçalho de Sucesso */}
      <div className="text-center mb-10">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: "spring", stiffness: 200, damping: 15 }}
          className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6"
        >
          <CheckCircle2 className="w-10 h-10 text-green-600" />
        </motion.div>
        
        <h2 className="text-2xl font-semibold text-gray-900 mb-2">
          Processamento Concluído
        </h2>
        <p className="text-gray-500">
          {data?.length || 0} registro{data?.length !== 1 ? 's' : ''} encontrado{data?.length !== 1 ? 's' : ''}
        </p>
      </div>

      {/* Card da Tabela */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden"
      >
        {/* Header do Card */}
        <div className="px-6 py-4 bg-gradient-to-r from-gray-50 to-white border-b border-gray-100">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-gray-900">Dados Extraídos</h3>
            <span className="text-sm text-gray-500">
              Total: <span className="font-semibold text-gray-900">{formatCurrency(total)}</span>
            </span>
          </div>
        </div>

        {/* Lista de Registros */}
        <div className="divide-y divide-gray-100">
          {data && data.length > 0 ? (
            data.map((item, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 * index }}
                className="hover:bg-blue-50/30 transition-colors"
              >
                {/* Linha Principal */}
                <div 
                  className="px-6 py-4 cursor-pointer flex items-center justify-between"
                  onClick={() => toggleRow(index)}
                >
                  <div className="flex items-center gap-6 flex-1">
                    {/* Banco */}
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                        <Building2 className="w-5 h-5 text-blue-600" />
                      </div>
                      <div>
                        <div className="text-xs text-gray-500">Banco</div>
                        <div className="font-medium text-gray-900">{item.banco || 'BB'}</div>
                      </div>
                    </div>

                    {/* Agência */}
                    <div>
                      <div className="text-xs text-gray-500 flex items-center gap-1">
                        <MapPin className="w-3 h-3" />
                        Agência
                      </div>
                      <div className="font-mono text-gray-900">{item.agencia || '-'}</div>
                    </div>

                    {/* Conta */}
                    <div>
                      <div className="text-xs text-gray-500 flex items-center gap-1">
                        <CreditCard className="w-3 h-3" />
                        Conta
                      </div>
                      <div className="font-mono text-gray-900">{item.conta || '-'}</div>
                    </div>

                    {/* Mês Referência (se investimento) */}
                    {isInvestmentExtract(item) && item.mes_referencia && (
                      <div>
                        <div className="text-xs text-gray-500 flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          Mês/Ano
                        </div>
                        <div className="font-medium text-gray-900">{item.mes_referencia}</div>
                      </div>
                    )}

                    {/* Saldo/Valor */}
                    <div className="ml-auto">
                      <div className="text-xs text-gray-500 flex items-center gap-1 justify-end">
                        <Wallet className="w-3 h-3" />
                        {isInvestmentExtract(item) ? 'Saldo Atual' : 'Valor'}
                      </div>
                      <div className="font-semibold text-gray-900 text-right">
                        {isInvestmentExtract(item) 
                          ? formatCurrency(item.valores_principais?.saldo_atual)
                          : formatCurrency(item.valor)
                        }
                      </div>
                    </div>
                  </div>

                  {/* Botão Expandir */}
                  <div className="ml-4">
                    {expandedRows[index] ? (
                      <ChevronUp className="w-5 h-5 text-gray-400" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-gray-400" />
                    )}
                  </div>
                </div>

                {/* Detalhes Expandidos */}
                <AnimatePresence>
                  {expandedRows[index] && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.3 }}
                      className="overflow-hidden"
                    >
                      <div className="px-6 pb-6 pt-2 bg-gray-50/50">
                        {isInvestmentExtract(item) ? (
                          /* Detalhes de Extrato de Investimento */
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {/* Valores Principais */}
                            {item.valores_principais && (
                              <div className="bg-white rounded-lg p-4 shadow-sm">
                                <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                                  <DollarSign className="w-4 h-4 text-green-600" />
                                  Resumo Financeiro
                                </h4>
                                <div className="space-y-2 text-sm">
                                  <div className="flex justify-between">
                                    <span className="text-gray-600">Saldo Anterior:</span>
                                    <span className="font-mono font-medium">{formatCurrency(item.valores_principais.saldo_anterior)}</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-gray-600">Aplicações (+):</span>
                                    <span className="font-mono font-medium text-green-600">{formatCurrency(item.valores_principais.aplicacoes)}</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-gray-600">Resgates (-):</span>
                                    <span className="font-mono font-medium text-red-600">{formatCurrency(item.valores_principais.resgates)}</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-gray-600">Rendimento Bruto:</span>
                                    <span className="font-mono font-medium text-blue-600">{formatCurrency(item.valores_principais.rendimento_bruto)}</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-gray-600">Imposto de Renda (-):</span>
                                    <span className="font-mono font-medium">{formatCurrency(item.valores_principais.imposto_renda)}</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-gray-600">IOF (-):</span>
                                    <span className="font-mono font-medium">{formatCurrency(item.valores_principais.iof)}</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-gray-600">Rendimento Líquido:</span>
                                    <span className="font-mono font-medium text-green-600">{formatCurrency(item.valores_principais.rendimento_liquido)}</span>
                                  </div>
                                  <div className="pt-2 mt-2 border-t border-gray-200 flex justify-between">
                                    <span className="font-semibold text-gray-900">Saldo Atual:</span>
                                    <span className="font-mono font-bold text-blue-700">{formatCurrency(item.valores_principais.saldo_atual)}</span>
                                  </div>
                                </div>
                              </div>
                            )}

                            {/* Rentabilidade */}
                            {item.rentabilidade && (
                              <div className="bg-white rounded-lg p-4 shadow-sm">
                                <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                                  <TrendingUp className="w-4 h-4 text-purple-600" />
                                  Rentabilidade
                                </h4>
                                <div className="space-y-2 text-sm">
                                  <div className="flex justify-between">
                                    <span className="text-gray-600">No Mês:</span>
                                    <span className="font-mono font-medium text-purple-600">{formatPercent(item.rentabilidade.no_mes)}</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-gray-600">No Ano:</span>
                                    <span className="font-mono font-medium text-purple-600">{formatPercent(item.rentabilidade.no_ano)}</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-gray-600">Últimos 12 Meses:</span>
                                    <span className="font-mono font-medium text-purple-600">{formatPercent(item.rentabilidade.ultimos_12_meses)}</span>
                                  </div>
                                </div>

                                {/* Valor da Cota */}
                                {item.valor_cota && item.valor_cota.length > 0 && (
                                  <div className="mt-4 pt-4 border-t border-gray-200">
                                    <h5 className="text-xs font-semibold text-gray-700 mb-2">Valor da Cota</h5>
                                    <div className="space-y-1 text-xs">
                                      {item.valor_cota.map((cota, idx) => (
                                        <div key={idx} className="flex justify-between">
                                          <span className="text-gray-500">{cota.data || '-'}:</span>
                                          <span className="font-mono">{cota.valor ? cota.valor.toFixed(9) : '-'}</span>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        ) : (
                          /* Detalhes de Extrato Bancário Comum */
                          <div className="bg-white rounded-lg p-4 shadow-sm">
                            <h4 className="font-semibold text-gray-900 mb-3">Detalhes da Conta</h4>
                            <div className="grid grid-cols-2 gap-4 text-sm">
                              {item.tipo_conta && (
                                <div>
                                  <span className="text-gray-600">Tipo de Conta:</span>
                                  <div className="font-medium">{item.tipo_conta}</div>
                                </div>
                              )}
                              {item.cpf_cnpj && (
                                <div>
                                  <span className="text-gray-600">CPF/CNPJ:</span>
                                  <div className="font-mono font-medium">{item.cpf_cnpj}</div>
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            ))
          ) : (
            <div className="px-6 py-12 text-center text-gray-500">
              Nenhum registro encontrado
            </div>
          )}
        </div>
      </motion.div>

      {/* Botões de Ação */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="flex flex-col sm:flex-row gap-4 mt-8 justify-center"
      >
        <motion.button
          onClick={onExport}
          disabled={isExporting || !data?.length}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className={`
            flex items-center justify-center gap-3 px-8 py-4 rounded-xl font-semibold
            transition-all duration-300 shadow-lg
            ${data?.length && !isExporting
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
