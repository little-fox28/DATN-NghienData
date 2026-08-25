import { Button, message } from 'antd';
import { CheckCircle2, Clock, Download, FileText, RefreshCw, XCircle } from 'lucide-react';
import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useSearchParams } from 'react-router-dom';
import { deleteLoanRecord, getEnrichedRecords, updateLoanRecord, updateRecordLabel } from '../api/client';
import { UnderwritingQueueTable } from '../components/dashboard/UnderwritingQueueTable';
import type { EnrichedRecordItem } from '../types/loan';

export const UnderwritingPage: React.FC = () => {
  const { t } = useTranslation();
  const [searchParams, setSearchParams] = useSearchParams();
  
  const initialSource = (searchParams.get('source') as 'all' | 'backlog' | 'live') || 'backlog';
  const [activeSource, setActiveSource] = useState<'all' | 'backlog' | 'live'>(initialSource);
  
  const [loading, setLoading] = useState<boolean>(true);
  const [records, setRecords] = useState<EnrichedRecordItem[]>([]);
  const [totalRecords, setTotalRecords] = useState<number>(0);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(20);
  const [backlogCount, setBacklogCount] = useState<number>(10084);
  const [liveCount, setLiveCount] = useState<number>(1);

  const fetchUnderwritingData = async (
    page = currentPage,
    size = pageSize,
    source = activeSource
  ) => {
    try {
      setLoading(true);
      const res = await getEnrichedRecords({
        page,
        pageSize: size,
        source,
      });
      if (res?.records) {
        setRecords(res.records);
        setTotalRecords(res.total || res.records.length);
        if (res.backlog_count) setBacklogCount(res.backlog_count);
        if (res.live_count !== undefined) setLiveCount(res.live_count);
      }
    } catch (err) {
      console.error('Error loading underwriting queue:', err);
      message.error(t('underwriting.errors.loadFailed', 'Không thể tải hàng đợi thẩm định.'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUnderwritingData(currentPage, pageSize, activeSource);
  }, [currentPage, pageSize, activeSource]);

  const handleSourceChange = (newSource: 'all' | 'backlog' | 'live') => {
    setActiveSource(newSource);
    setCurrentPage(1);
    setSearchParams({ source: newSource });
  };

  const handlePageChange = (page: number, size: number) => {
    setCurrentPage(page);
    setPageSize(size);
  };

  // [U] Approve Action
  const handleApprove = async (record: EnrichedRecordItem) => {
    if (!record.client_ID) return;
    try {
      await updateRecordLabel(record.client_ID, 0);
      message.success(t('underwriting.messages.labelUpdated', { id: record.client_ID }));
      fetchUnderwritingData(currentPage, pageSize, activeSource);
    } catch (err) {
      console.error('Error approving record:', err);
      message.error(t('underwriting.errors.updateFailed', 'Lỗi cập nhật trạng thái hồ sơ.'));
    }
  };

  // [U] Reject Action
  const handleReject = async (record: EnrichedRecordItem) => {
    if (!record.client_ID) return;
    try {
      await updateRecordLabel(record.client_ID, 1);
      message.success(t('underwriting.messages.labelUpdated', { id: record.client_ID }));
      fetchUnderwritingData(currentPage, pageSize, activeSource);
    } catch (err) {
      console.error('Error rejecting record:', err);
      message.error(t('underwriting.errors.updateFailed', 'Lỗi cập nhật trạng thái hồ sơ.'));
    }
  };

  // [U] Modify Details Action
  const handleModify = async (clientId: string, updates: Partial<EnrichedRecordItem>) => {
    try {
      await updateLoanRecord(clientId, updates);
      message.success(t('underwriting.messages.modifySuccess', 'Đã cập nhật thông tin và điều kiện khoản vay thành công.'));
      fetchUnderwritingData(currentPage, pageSize, activeSource);
    } catch (err) {
      console.error('Error updating record:', err);
      message.error(t('underwriting.errors.modifyFailed', 'Lỗi khi cập nhật thông tin khoản vay.'));
    }
  };

  // [D] Delete Action
  const handleDelete = async (record: EnrichedRecordItem) => {
    if (!record.client_ID) return;
    try {
      await deleteLoanRecord(record.client_ID);
      message.success(t('underwriting.messages.deleteSuccess', 'Đã xóa hồ sơ khoản vay khỏi hàng đợi.'));
      fetchUnderwritingData(currentPage, pageSize, activeSource);
    } catch (err) {
      console.error('Error deleting record:', err);
      message.error(t('underwriting.errors.deleteFailed', 'Lỗi khi xóa hồ sơ.'));
    }
  };

  // Batch Approve
  const handleBatchApprove = async (selected: EnrichedRecordItem[]) => {
    try {
      setLoading(true);
      for (const item of selected) {
        if (item.client_ID) {
          await updateRecordLabel(item.client_ID, 0);
        }
      }
      message.success(t('underwriting.batch.successApprove', { count: selected.length }));
      fetchUnderwritingData(currentPage, pageSize, activeSource);
    } catch (err) {
      console.error('Error batch approving:', err);
      message.error(t('underwriting.errors.updateFailed', 'Lỗi thẩm định hàng loạt.'));
    } finally {
      setLoading(false);
    }
  };

  // Batch Reject
  const handleBatchReject = async (selected: EnrichedRecordItem[]) => {
    try {
      setLoading(true);
      for (const item of selected) {
        if (item.client_ID) {
          await updateRecordLabel(item.client_ID, 1);
        }
      }
      message.success(t('underwriting.batch.successReject', { count: selected.length }));
      fetchUnderwritingData(currentPage, pageSize, activeSource);
    } catch (err) {
      console.error('Error batch rejecting:', err);
      message.error(t('underwriting.errors.updateFailed', 'Lỗi thẩm định hàng loạt.'));
    } finally {
      setLoading(false);
    }
  };

  const handleExportCSV = () => {
    window.open(`${import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'}/api/v1/enrich/export`, '_blank');
  };

  // Operational statistics
  const displayedTotal = activeSource === 'backlog' ? backlogCount : totalRecords;
  const manualCases = activeSource === 'backlog' ? backlogCount : records.filter(r => r.ml_decision === 'MANUAL_REVIEW').length;
  const approvedCases = records.filter(r => r.ml_decision === 'APPROVED' || r.ml_decision === 'APPROVED_CONDITIONAL').length;
  const rejectedCases = records.filter(r => r.ml_decision === 'REJECTED').length;

  const kpis = [
    {
      title: t('underwriting.kpi.totalInQueue', 'Tổng Hồ Sơ Trong Hàng Đợi'),
      value: displayedTotal.toLocaleString(),
      subtext: `${backlogCount.toLocaleString()} backlog • ${liveCount} live stream`,
      icon: FileText,
      color: 'text-indigo-500 bg-indigo-50 dark:bg-indigo-950/40 border-indigo-200 dark:border-indigo-900/60',
    },
    {
      title: t('underwriting.kpi.manualReview', 'Cần Thẩm Định Thủ Công'),
      value: manualCases.toLocaleString(),
      subtext: t('underwriting.kpi.borderlineWarning', 'Vùng đệm rủi ro (Grade C-D)'),
      icon: Clock,
      color: 'text-amber-500 bg-amber-50 dark:bg-amber-950/40 border-amber-200 dark:border-amber-900/60',
    },
    {
      title: t('underwriting.kpi.autoApproved', 'Đã Phê Duyệt'),
      value: approvedCases.toLocaleString(),
      subtext: t('underwriting.kpi.streamActive', 'Đang cập nhật thời gian thực'),
      icon: CheckCircle2,
      color: 'text-emerald-500 bg-emerald-50 dark:bg-emerald-950/40 border-emerald-200 dark:border-emerald-900/60',
    },
    {
      title: t('underwriting.kpi.rejected', 'Đã Từ Chối'),
      value: rejectedCases.toLocaleString(),
      subtext: t('underwriting.kpi.highRiskDesc', 'Vượt ngưỡng rủi ro cho phép'),
      icon: XCircle,
      color: 'text-rose-500 bg-rose-50 dark:bg-rose-950/40 border-rose-200 dark:border-rose-900/60',
    },
  ];

  return (
    <div className="w-full space-y-6 pb-8">
      {/* 1. Header Workspace Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-gray-200 dark:border-[#2a2a2a]">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight mt-1">
            {t('underwriting.title', 'Hàng Đợi Thẩm Định & Phân Tích Hồ Sơ Vay')}
          </h1>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {t('underwriting.subtitle', 'Không gian làm việc cho Thẩm định viên: Mổ xẻ chi tiết tín hiệu XAI, kiểm tra hồ sơ và phê duyệt hạn mức thủ công')}
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            icon={<RefreshCw className="w-3.5 h-3.5" />}
            onClick={() => fetchUnderwritingData(currentPage, pageSize, activeSource)}
            loading={loading}
            className="flex items-center gap-1.5 font-medium"
          >
            {t('dashboard.buttons.refresh', 'Làm mới')}
          </Button>

          <Button
            type="primary"
            icon={<Download className="w-3.5 h-3.5" />}
            onClick={handleExportCSV}
            className="bg-indigo-600 hover:bg-indigo-500 border-none font-medium flex items-center gap-1.5"
          >
            {t('dashboard.buttons.export', 'Xuất Báo Cáo (CSV)')}
          </Button>
        </div>
      </div>

      {/* 2. Operational KPIs */}
      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.map((kpi, idx) => {
          const IconComp = kpi.icon;
          return (
            <div
              key={idx}
              className="bg-white dark:bg-[#141414] rounded-lg border border-gray-200 dark:border-[#2a2a2a] p-4 shadow-xs transition-colors flex flex-col justify-between"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  {kpi.title}
                </span>
                <div className={`p-2 rounded-lg border ${kpi.color}`}>
                  <IconComp className="w-4 h-4" />
                </div>
              </div>
              <div>
                <div className="text-2xl font-bold text-slate-900 dark:text-white font-mono">
                  {loading ? '...' : kpi.value}
                </div>
                <div className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                  {kpi.subtext}
                </div>
              </div>
            </div>
          );
        })}
      </section>

      {/* 3. Main Underwriting Queue Table & Case Inspection */}
      <section>
        <UnderwritingQueueTable
          records={records}
          totalRecords={totalRecords}
          currentPage={currentPage}
          pageSize={pageSize}
          loading={loading}
          activeSource={activeSource}
          onSourceChange={handleSourceChange}
          onPageChange={handlePageChange}
          onRefresh={() => fetchUnderwritingData(currentPage, pageSize, activeSource)}
          onApprove={handleApprove}
          onReject={handleReject}
          onDelete={handleDelete}
          onModify={handleModify}
          onBatchApprove={handleBatchApprove}
          onBatchReject={handleBatchReject}
        />
      </section>
    </div>
  );
};
