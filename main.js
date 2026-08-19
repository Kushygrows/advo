const { app, BrowserWindow, shell, session } = require("electron");
const path = require("path");

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 900,
    minWidth: 720,
    minHeight: 600,
    title: "Advo",
    icon: path.join(__dirname, "build", process.platform === "win32" ? "icon.ico" : "icon.png"),
    autoHideMenuBar: true,
    backgroundColor: "#1a1a1c",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    }
  });

  win.loadFile(path.join(__dirname, "advo.html"));

  // Anything that tries to open a new window/tab (search-engine queries,
  // source citation links, the "Look up a source" link, the tutorial
  // video) should open in the user's normal system browser or default
  // app instead of inside Advo.
  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });

  return win;
}

app.whenReady().then(() => {
  // Advo is a single trusted local app you launch yourself, not a random
  // website — allow the clipboard permissions its Copy buttons rely on
  // without popping a permission prompt every time.
  session.defaultSession.setPermissionRequestHandler((webContents, permission, callback) => {
    callback(["clipboard-read", "clipboard-sanitized-write"].includes(permission));
  });

  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
