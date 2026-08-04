import type {
  FullDataBackupDocument,
  FullDataBackupExportResponse,
  FullDataBackupPreviewResponse,
  FullDataBackupRestoreResponse,
} from '../types/fullDataBackup';
import apiClient from './index';

type PreviewWireResponse = {
  manifest: Record<string, unknown>;
  warnings?: string[];
  preview_token: string;
  incoming_digest: string;
  destination_digest: string;
  issued_at: string;
  expires_at: string;
  incoming_table_row_counts: Record<string, number>;
  destination_table_row_counts: Record<string, number>;
  restart_required: boolean;
};

type RestoreWireResponse = {
  success: boolean;
  incoming_digest: string;
  destination_digest_before: string;
  destination_digest_after: string;
  restored_table_row_counts: Record<string, number>;
  recovery_filename: string;
  recovery: {
    filename: string;
    digest: string;
    destination_digest: string;
  };
  warnings?: string[];
  restart_required: boolean;
};

function transformExportResponse(
  content: unknown,
  _headers: unknown,
  status?: number,
): unknown {
  if (status === undefined || (status >= 200 && status < 300)) {
    return content;
  }
  if (typeof content !== 'string') {
    return content;
  }
  try {
    const parsed: unknown = JSON.parse(content);
    return parsed && typeof parsed === 'object' && !Array.isArray(parsed)
      ? parsed
      : undefined;
  } catch {
    return undefined;
  }
}

export const fullDataBackupApi = {
  async exportBackup(): Promise<FullDataBackupExportResponse> {
    const response = await apiClient.get<string>(
      '/api/v1/system/full-data-backup/export',
      {
        responseType: 'text',
        transformResponse: [transformExportResponse],
      },
    );
    const disposition = String(response.headers['content-disposition'] || '');
    const match = disposition.match(/filename="?([^";]+)"?/i);
    return {
      fileName: match?.[1] || 'pp02-full-data-backup.json',
      content: response.data,
    };
  },

  async previewRestore(
    backup: FullDataBackupDocument,
  ): Promise<FullDataBackupPreviewResponse> {
    const response = await apiClient.post<PreviewWireResponse>(
      '/api/v1/system/full-data-backup/preview',
      backup,
    );
    const data = response.data;
    return {
      manifest: data.manifest,
      warnings: data.warnings || [],
      previewToken: data.preview_token,
      incomingDigest: data.incoming_digest,
      destinationDigest: data.destination_digest,
      issuedAt: data.issued_at,
      expiresAt: data.expires_at,
      incomingTableRowCounts: data.incoming_table_row_counts,
      destinationTableRowCounts: data.destination_table_row_counts,
      restartRequired: data.restart_required,
    };
  },

  async restore(payload: {
    backup: FullDataBackupDocument;
    previewToken: string;
  }): Promise<FullDataBackupRestoreResponse> {
    const response = await apiClient.post<RestoreWireResponse>(
      '/api/v1/system/full-data-backup/restore',
      {
        backup: payload.backup,
        preview_token: payload.previewToken,
      },
    );
    const data = response.data;
    return {
      success: data.success,
      incomingDigest: data.incoming_digest,
      destinationDigestBefore: data.destination_digest_before,
      destinationDigestAfter: data.destination_digest_after,
      restoredTableRowCounts: data.restored_table_row_counts,
      recoveryFilename: data.recovery_filename,
      recovery: {
        filename: data.recovery.filename,
        digest: data.recovery.digest,
        destinationDigest: data.recovery.destination_digest,
      },
      warnings: data.warnings || [],
      restartRequired: data.restart_required,
    };
  },
};
