import { Button, Input, Radio, Select, Table, Tag } from 'antd';
import { CheckCircle2, Eye, RefreshCw, Search, ShieldCheck, XCircle } from 'lucide-react';
import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { EnrichedRecordItem } from '../../types/loan';
import { CaseInspectionModal } from './CaseInspectionDrawer';

interface UnderwritingQueueTableProps {
  records?: EnrichedRecordItem[];
  totalRecords?: number;
  currentPage?: number;
  pageSize?: number;
  loading?: boolean;
  activeSource?: 'all' | 'backlog' | 'live';
  onSourceChange?: (source: 'all' | 'backlog' | 'live') => void;
  onPageChange?: (page: number, pageSize: number) => void;
  onRefresh?: () => void;
  onApprove?: (record: EnrichedRecordItem) => void;
  onReject?: (record: EnrichedRecordItem) => void;
  onDelete?: (record: EnrichedRecordItem) => void;
  onModify?: (clientId: string, updates: Partial<EnrichedRecordItem>) => void;
  onBatchApprove?: (records: EnrichedRecordItem[]) => void;
  onBatchReject?: (records: EnrichedRecordItem[]) => void;
}

export const UnderwritingQueueTable: React.FC<UnderwritingQueueTableProps> = ({
  records = [],
  totalRecords = 0,
  currentPage = 1,
  pageSize = 10,
  loading,
  activeSource = 'all',
  onSourceChange,
  onPageChange,
  onRefresh,
  onApprove,
  onReject,
  onDelete,
  onModify,
  onBatchApprove,
  onBatchReject,
}) => {
  const { t } = useTranslation();
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedGrade, setSelectedGrade] = useState<string>('ALL');
  const [selectedDecision, setSelectedDecision] = useState<string>('ALL');
  const [inspectingRecord, setInspectingRecord] = useState<EnrichedRecordItem | null>(null);
  const [modalOpen, setModalOpen] = useState<boolean>(false);
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);

  // Filtering local slice (when searching on page)
  const filteredData = records.filter((item) => {
    const matchSearch =
      searchTerm.trim() === '' ||
      (item.application_id && item.application_id.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (item.client_ID && item.client_ID.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (item.loan_intent && item.loan_intent.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchGrade = selectedGrade === 'ALL' || item.loan_grade === selectedGrade;
    const matchDecision = selectedDecision === 'ALL' || item.ml_decision === selectedDecision;

    return matchSearch && matchGrade && matchDecision;
  });

  const getFicoColor = (score: number) => {
    if (score >= 740) return 'text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/50 border-emerald-200 dark:border-emerald-900/60';
    if (score >= 670) return 'text-teal-600 dark:text-teal-400 bg-teal-50 dark:bg-teal-950/50 border-teal-200 dark:border-teal-900/60';
    if (score >= 580) return 'text-amber-500 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/50 border-amber-200 dark:border-amber-900/60';
    return 'text-rose-500 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/50 border-rose-200 dark:border-rose-900/60';
  };

  const getDecisionTag = (decision: string) => {
    switch (decision) {
      case 'APPROVED':
        return <Tag color="success">APPROVED</Tag>;
      case 'APPROVED_CONDITIONAL':
        return <Tag color="cyan">CONDITIONAL</Tag>;
      case 'MANUAL_REVIEW':
        return <Tag color="warning">MANUAL REVIEW</Tag>;
      case 'REJECTED':
        return <Tag color="error">REJECTED</Tag>;
      default:
        return <Tag>{decision}</Tag>;
    }
  };

  const handleInspect = (record: EnrichedRecordItem) => {
    setInspectingRecord(record);
    setModalOpen(true);
  };

  const selectedRecords = filteredData.filter(r => 
    selectedRowKeys.includes(r.application_id || r.client_ID || '')
  );

  const handleExecuteBatchApprove = () => {
    if (onBatchApprove && selectedRecords.length > 0) {
      onBatchApprove(selectedRecords);
      setSelectedRowKeys([]);
    }
  };

  const handleExecuteBatchReject = () => {
    if (onBatchReject && selectedRecords.length > 0) {
      onBatchReject(selectedRecords);
      setSelectedRowKeys([]);
    }
  };

  const rowSelection = {
    selectedRowKeys,
    onChange: (keys: React.Key[]) => setSelectedRowKeys(keys),
  };

  const columns = [
    {
      title: t('underwriting.table.appClient', 'Mã Hồ Sơ / Khách Hàng'),
      key: 'id',
      render: (_: any, r: EnrichedRecordItem) => (
        <div className="flex flex-col">
          <span className="font-mono font-bold text-slate-900 dark:text-gray-100 text-xs">
            {r.application_id || r.client_ID}
          </span>
          <span className="text-[10px] text-gray-400 dark:text-gray-500 font-mono">
            {r.client_ID} • {r.loan_intent}
          </span>
        </div>
      ),
    },
    {
      title: t('underwriting.table.incomeLoan', 'Thu Nhập / Khoản Vay'),
      key: 'financial',
      render: (_: any, r: EnrichedRecordItem) => (
        <div className="flex flex-col text-xs font-mono">
          <span className="font-bold text-slate-900 dark:text-gray-100">
            ${Number(r.loan_amnt || 0).toLocaleString()}
          </span>
          <span className="text-[10px] text-gray-400 dark:text-gray-500">
            {t('underwriting.table.incomePrefix', 'Thu nhập:')} ${Number(r.person_income || 0).toLocaleString()}
          </span>
        </div>
      ),
    },
    {
      title: t('underwriting.table.gradeTerm', 'Hạng / Kỳ Hạn'),
      key: 'term',
      render: (_: any, r: EnrichedRecordItem) => (
        <div className="flex items-center gap-2 text-xs">
          <span className={`px-1.5 py-0.5 rounded font-bold text-xs ${
            r.loan_grade === 'C' ? 'bg-amber-100 dark:bg-amber-950/80 text-amber-800 dark:text-amber-300' :
            r.loan_grade === 'D' ? 'bg-rose-100 dark:bg-rose-950/80 text-rose-800 dark:text-rose-300' :
            'bg-gray-100 dark:bg-[#1f1f1f] text-slate-800 dark:text-gray-200'
          }`}>
            {r.loan_grade}
          </span>
          <span className="text-gray-500 dark:text-gray-400 font-mono text-[11px]">
            {r.loan_term_months || 36}m ({r.loan_int_rate}%)
          </span>
        </div>
      ),
    },
    {
      title: t('underwriting.table.ficoScore', 'Điểm FICO'),
      key: 'fico',
      render: (_: any, r: EnrichedRecordItem) => {
        const score = Number(r.ml_credit_score) > 0 ? Number(r.ml_credit_score) : 640;
        return (
          <span className={`px-2 py-0.5 rounded font-bold font-mono text-xs border ${getFicoColor(score)}`}>
            {score}
          </span>
        );
      },
    },
    {
      title: t('underwriting.table.pdScore', 'Xác Suất PD'),
      key: 'pd',
      render: (_: any, r: EnrichedRecordItem) => {
        const rawPd = Number(r.ml_pd_score) || 0.068;
        const pd = (rawPd > 1 ? rawPd : rawPd * 100);
        return (
          <span className={`font-mono text-xs font-semibold ${pd <= 5 ? 'text-emerald-600 dark:text-emerald-400' : pd <= 10 ? 'text-amber-500 dark:text-amber-400' : 'text-rose-500 dark:text-rose-400'}`}>
            {pd.toFixed(2)}%
          </span>
        );
      },
    },
    {
      title: t('underwriting.table.mlDecision', 'Quyết Định ML'),
      key: 'decision',
      render: (_: any, r: EnrichedRecordItem) => getDecisionTag(r.ml_decision || 'MANUAL_REVIEW'),
    },
    {
      title: t('underwriting.table.action', 'Thao Tác'),
      key: 'action',
      align: 'center' as const,
      render: (_: any, r: EnrichedRecordItem) => (
        <Button
          size="small"
          type="primary"
          icon={<Eye className="w-3.5 h-3.5" />}
          className="bg-indigo-600 hover:bg-indigo-500 border-none font-medium flex items-center gap-1 mx-auto"
          onClick={() => handleInspect(r)}
        >
          {t('underwriting.buttons.inspect', 'Thẩm định')}
        </Button>
      ),
    },
  ];

  return (
    <div className="bg-white dark:bg-[#141414] rounded-lg border border-gray-200 dark:border-[#2a2a2a] p-4 shadow-xs transition-colors space-y-4">
      {/* Table Header & Source Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-gray-100 dark:border-[#262626]">
        <div>
          <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wide flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-indigo-500" />
            {t('underwriting.queue.title', 'Hàng Đợi Thẩm Định Tín Dụng & Nhật Ký Hồ Sơ')}
          </h3>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {t('underwriting.queue.subtitle', 'Danh sách hồ sơ tín dụng trực tuyến, phân tích chuyên sâu điểm FICO và XAI')}
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          {/* Source Tabs */}
          {onSourceChange && (
            <Radio.Group
              value={activeSource}
              onChange={(e) => onSourceChange(e.target.value)}
              size="small"
              buttonStyle="solid"
            >
              <Radio.Button value="backlog">
                <span className="font-semibold">{t('underwriting.sources.backlog', 'Hồ sơ Cần Thẩm định (10,084 Backlog)')}</span>
              </Radio.Button>
              <Radio.Button value="all">
                {t('underwriting.sources.all', 'Tất cả')}
              </Radio.Button>
              <Radio.Button value="live">
                {t('underwriting.sources.live', 'Trực tuyến (Live)')}
              </Radio.Button>
            </Radio.Group>
          )}

          {onRefresh && (
            <Button
              icon={<RefreshCw className="w-3.5 h-3.5" />}
              size="small"
              onClick={onRefresh}
              loading={loading}
            >
              {t('dashboard.buttons.refresh', 'Làm mới')}
            </Button>
          )}
        </div>
      </div>

      {/* Filter Bar & Batch Action Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 flex-1">
          <div>
            <Input
              placeholder={t('underwriting.search.placeholder', 'Tìm theo Mã Hồ Sơ, Client ID...')}
              prefix={<Search className="w-3.5 h-3.5 text-gray-400 dark:text-gray-500" />}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              allowClear
              size="middle"
            />
          </div>

          <div>
            <Select
              className="w-full"
              value={selectedGrade}
              onChange={setSelectedGrade}
              size="middle"
              options={[
                { value: 'ALL', label: t('underwriting.filter.allGrades', 'Tất cả Hạng (Grade A-G)') },
                { value: 'A', label: t('underwriting.filter.gradeA', 'Grade A (VIP Prime)') },
                { value: 'B', label: t('underwriting.filter.gradeB', 'Grade B (Standard)') },
                { value: 'C', label: t('underwriting.filter.gradeC', 'Grade C (Near Prime)') },
                { value: 'D', label: t('underwriting.filter.gradeD', 'Grade D (Borderline)') },
                { value: 'E', label: t('underwriting.filter.gradeE', 'Grade E (Subprime)') },
                { value: 'F', label: t('underwriting.filter.gradeF', 'Grade F') },
                { value: 'G', label: t('underwriting.filter.gradeG', 'Grade G (High Risk)') },
              ]}
            />
          </div>

          <div>
            <Select
              className="w-full"
              value={selectedDecision}
              onChange={setSelectedDecision}
              size="middle"
              options={[
                { value: 'ALL', label: t('underwriting.filter.allDecisions', 'Tất cả Quyết định ML') },
                { value: 'APPROVED', label: t('underwriting.filter.decisionApproved', 'APPROVED (Phê duyệt)') },
                { value: 'APPROVED_CONDITIONAL', label: t('underwriting.filter.decisionConditional', 'APPROVED CONDITIONAL (Có điều kiện)') },
                { value: 'MANUAL_REVIEW', label: t('underwriting.filter.decisionManual', 'MANUAL REVIEW (Cần thẩm định)') },
                { value: 'REJECTED', label: t('underwriting.filter.decisionRejected', 'REJECTED (Từ chối)') },
              ]}
            />
          </div>
        </div>

        {/* Batch Action Toolbar */}
        {selectedRowKeys.length > 0 && (
          <div className="flex items-center gap-2 bg-indigo-50 dark:bg-indigo-950/50 border border-indigo-200 dark:border-indigo-900/60 p-1.5 px-3 rounded-lg animate-fade-in">
            <span className="text-xs font-semibold text-indigo-700 dark:text-indigo-300">
              {t('underwriting.batch.selected', { count: selectedRowKeys.length })}
            </span>
            <Button
              type="primary"
              size="small"
              icon={<CheckCircle2 className="w-3.5 h-3.5" />}
              className="bg-emerald-600 hover:bg-emerald-500 border-none text-xs font-medium"
              onClick={handleExecuteBatchApprove}
            >
              {t('underwriting.batch.approve', 'Phê duyệt Hàng loạt')}
            </Button>
            <Button
              danger
              size="small"
              icon={<XCircle className="w-3.5 h-3.5" />}
              className="text-xs font-medium"
              onClick={handleExecuteBatchReject}
            >
              {t('underwriting.batch.reject', 'Từ chối Hàng loạt')}
            </Button>
          </div>
        )}
      </div>

      {/* Table with Row Selection & Pagination */}
      <div className="overflow-x-auto">
        <Table
          rowSelection={rowSelection}
          dataSource={filteredData}
          columns={columns}
          rowKey={(r) => r.application_id || r.client_ID || Math.random().toString()}
          pagination={{
            current: currentPage,
            pageSize: pageSize,
            total: totalRecords || filteredData.length,
            showSizeChanger: true,
            pageSizeOptions: ['10', '20', '50', '100'],
            onChange: (page, size) => {
              if (onPageChange) onPageChange(page, size);
            },
            showTotal: (total, range) => t('underwriting.notices.paginationTotal', { start: range[0], end: range[1], total }),
          }}
          size="middle"
          loading={loading}
        />
      </div>

      {/* Case Inspection Modal with Complete Underwriter Decision Options */}
      <CaseInspectionModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        record={inspectingRecord}
        onApprove={onApprove}
        onReject={onReject}
        onDelete={onDelete}
        onModify={onModify}
      />
    </div>
  );
};
