export type FullDataBackupDocument = {
  format: 'pp02.full-data.backup';
  format_version: 1;
  metadata: Record<string, unknown>;
  manifest: Record<string, unknown>;
  data: Record<string, unknown>;
  integrity: {
    algorithm: 'sha256';
    value: string;
  };
};

export type FullDataBackupPreviewResponse = {
  manifest: Record<string, unknown>;
  warnings: string[];
  previewToken: string;
  incomingDigest: string;
  destinationDigest: string;
  issuedAt: string;
  expiresAt: string;
  incomingTableRowCounts: Record<string, number>;
  destinationTableRowCounts: Record<string, number>;
  restartRequired: boolean;
};

export type FullDataBackupRestoreResponse = {
  success: boolean;
  incomingDigest: string;
  destinationDigestBefore: string;
  destinationDigestAfter: string;
  restoredTableRowCounts: Record<string, number>;
  recoveryFilename: string;
  recovery: {
    filename: string;
    digest: string;
    destinationDigest: string;
  };
  restartRequired: boolean;
};

export type FullDataBackupExportResponse = {
  fileName: string;
  content: string;
};
