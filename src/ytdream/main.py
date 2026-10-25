import sys, logging
from PySide6.QtWidgets import QApplication, QMessageBox
from .ui.main_window import MainWindow
from .utils.logging_setup import configure_logging

def main():
    configure_logging(); app=QApplication(sys.argv); app.setApplicationName("YTDream Downloader"); app.setOrganizationName("warlock-oss")
    try: window=MainWindow(); window.show(); return app.exec()
    except Exception as e:
        logging.exception("Fatal startup error"); QMessageBox.critical(None,"YTDream Downloader gagal dibuka",f"Aplikasi mengalami masalah saat memulai. Detail dicatat di log.\n\n{e}"); return 1
if __name__=="__main__": raise SystemExit(main())
