const { contextBridge, ipcRenderer } = require('electron');

const DESKTOP_VERSION_ARG_PREFIX = '--dsa-desktop-version=';
const DESKTOP_GET_UPDATE_STATE_CHANNEL = 'desktop:get-update-state';
const DESKTOP_CHECK_FOR_UPDATES_CHANNEL = 'desktop:check-for-updates';
const DESKTOP_INSTALL_DOWNLOADED_UPDATE_CHANNEL = 'desktop:install-downloaded-update';
const DESKTOP_OPEN_RELEASE_PAGE_CHANNEL = 'desktop:open-release-page';
const DESKTOP_UPDATE_STATE_EVENT = 'desktop:update-state';
const DESKTOP_GET_SECURE_CREDENTIAL_STATUS_CHANNEL = 'desktop:get-secure-credential-status';
const DESKTOP_PREPARE_SECURE_CREDENTIAL_UPDATE_CHANNEL = 'desktop:prepare-secure-credential-update';
const DESKTOP_COMMIT_SECURE_CREDENTIAL_UPDATE_CHANNEL = 'desktop:commit-secure-credential-update';
const DESKTOP_ROLLBACK_SECURE_CREDENTIAL_UPDATE_CHANNEL = 'desktop:rollback-secure-credential-update';
const DESKTOP_FINALIZE_SECURE_CREDENTIAL_UPDATE_CHANNEL = 'desktop:finalize-secure-credential-update';

function readDesktopVersion(argv = process.argv) {
  const versionArg = argv.find(
    (value) => typeof value === 'string' && value.startsWith(DESKTOP_VERSION_ARG_PREFIX)
  );
  return versionArg ? versionArg.slice(DESKTOP_VERSION_ARG_PREFIX.length) : '';
}

function createDesktopBridge({
  version = readDesktopVersion(),
  renderer = ipcRenderer,
} = {}) {
  return {
    version,
    getUpdateState() {
      return renderer.invoke(DESKTOP_GET_UPDATE_STATE_CHANNEL);
    },
    checkForUpdates() {
      return renderer.invoke(DESKTOP_CHECK_FOR_UPDATES_CHANNEL);
    },
    installDownloadedUpdate() {
      return renderer.invoke(DESKTOP_INSTALL_DOWNLOADED_UPDATE_CHANNEL);
    },
    openReleasePage(releaseUrl) {
      return renderer.invoke(DESKTOP_OPEN_RELEASE_PAGE_CHANNEL, releaseUrl);
    },
    getSecureCredentialStatus() {
      return renderer.invoke(DESKTOP_GET_SECURE_CREDENTIAL_STATUS_CHANNEL);
    },
    prepareSecureCredentialUpdate(payload) {
      return renderer.invoke(DESKTOP_PREPARE_SECURE_CREDENTIAL_UPDATE_CHANNEL, payload);
    },
    commitSecureCredentialUpdate(transactionId) {
      return renderer.invoke(DESKTOP_COMMIT_SECURE_CREDENTIAL_UPDATE_CHANNEL, transactionId);
    },
    rollbackSecureCredentialUpdate(transactionId) {
      return renderer.invoke(DESKTOP_ROLLBACK_SECURE_CREDENTIAL_UPDATE_CHANNEL, transactionId);
    },
    finalizeSecureCredentialUpdate(transactionId) {
      return renderer.invoke(DESKTOP_FINALIZE_SECURE_CREDENTIAL_UPDATE_CHANNEL, transactionId);
    },
    onUpdateStateChange(listener) {
      if (typeof listener !== 'function') {
        return () => undefined;
      }

      const handler = (_event, payload) => {
        listener(payload);
      };
      renderer.on(DESKTOP_UPDATE_STATE_EVENT, handler);
      return () => {
        renderer.removeListener(DESKTOP_UPDATE_STATE_EVENT, handler);
      };
    },
  };
}

contextBridge.exposeInMainWorld('dsaDesktop', createDesktopBridge());

module.exports = {
  DESKTOP_COMMIT_SECURE_CREDENTIAL_UPDATE_CHANNEL,
  DESKTOP_CHECK_FOR_UPDATES_CHANNEL,
  DESKTOP_FINALIZE_SECURE_CREDENTIAL_UPDATE_CHANNEL,
  DESKTOP_GET_SECURE_CREDENTIAL_STATUS_CHANNEL,
  DESKTOP_GET_UPDATE_STATE_CHANNEL,
  DESKTOP_INSTALL_DOWNLOADED_UPDATE_CHANNEL,
  DESKTOP_OPEN_RELEASE_PAGE_CHANNEL,
  DESKTOP_PREPARE_SECURE_CREDENTIAL_UPDATE_CHANNEL,
  DESKTOP_ROLLBACK_SECURE_CREDENTIAL_UPDATE_CHANNEL,
  DESKTOP_UPDATE_STATE_EVENT,
  DESKTOP_VERSION_ARG_PREFIX,
  createDesktopBridge,
  readDesktopVersion,
};
