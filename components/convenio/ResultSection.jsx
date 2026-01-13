import React from 'react';
import { motion } from 'framer-motion';
import { 
  CheckCircle2, 
  Download, 
  RotateCcw, 
  Building2, 
  MapPin, 
  CreditCard, 
  DollarSign,
  FileSpreadsheet
} from 'lucide-react';

/**
 * Componente de Resultado
 * Exibe tabela com dados extraídos e opções de exportação
 */
export default function ResultSection({ data, onExport, onNewUpload, isExporting }) {
  // Formata valor monetário
  const formatCurrency = (value) => {
    if (value === null || value === undefined) return '-';
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  // Calcula total
  const total = data?.reduce((sum, item) => sum + (item.valor || 0), 0) || 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="w-full max-w-4xl mx-auto"
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

        {/* Tabela */}
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50/50">
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  <div className="flex items-center gap-2">
                    <Building2 className="w-4 h-4" />
                    Banco
                  </div>
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4" />
                    Agência
                  </div>
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  <div className="flex items-center gap-2">
                    <CreditCard className="w-4 h-4" />
                    Conta
                  </div>
                </th>
                <th className="px-6 py-4 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  <div className="flex items-center justify-end gap-2">
                    <DollarSign className="w-4 h-4" />
                    Valor
                  </div>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data && data.length > 0 ? (
                data.map((item, index) => (
                  <motion.tr
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.1 * index }}
                    className="hover:bg-blue-50/30 transition-colors"
                  >
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                          <Building2 className="w-5 h-5 text-blue-600" />
                        </div>
                        <span className="font-medium text-gray-900">
                          {item.banco || '-'}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-gray-600 font-mono">
                      {item.agencia || '-'}
                    </td>
                    <td className="px-6 py-4 text-gray-600 font-mono">
                      {item.conta || '-'}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <span className="font-semibold text-gray-900">
                        {formatCurrency(item.valor)}
                      </span>
                    </td>
                  </motion.tr>
                ))
              ) : (
                <tr>
                  <td colSpan={4} className="px-6 py-12 text-center text-gray-500">
                    Nenhum registro encontrado
                  </td>
                </tr>
              )}
            </tbody>
            
            {/* Footer com Total */}
            {data && data.length > 0 && (
              <tfoot>
                <tr className="bg-gradient-to-r from-blue-50 to-indigo-50">
                  <td colSpan={3} className="px-6 py-4 text-right font-semibold text-gray-700">
                    Total Geral:
                  </td>
                  <td className="px-6 py-4 text-right">
                    <span className="text-lg font-bold text-blue-700">
                      {formatCurrency(total)}
                    </span>
                  </td>
                </tr>
              </tfoot>
            )}
          </table>
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
