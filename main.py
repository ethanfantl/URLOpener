import config
from ui.app import UrlManagerApp

if __name__ == "__main__":
    # Setup configuration first
    config.setup_logging()
    config.setup_theme()
    
    # Launch Application
    app = UrlManagerApp()
    app.mainloop()