import logging
import os
from PyQt5.QtWidgets import (QApplication, QComboBox, QGridLayout, QSizePolicy, QSpacerItem, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QFileDialog, QLabel, QProgressBar)
from PyQt5.QtCore import QThread, pyqtSignal
from QPlainTextEditLogger import QPlainTextEditLogger
from crawling import crawling
import sys

class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.thread = QThread()

    def initUI(self):
        self.setWindowTitle('Coupang&11st_ crawling')
        self.comp_log_folder = 'CompLog'

        if not os.path.exists(self.comp_log_folder):
            os.makedirs(self.comp_log_folder)
        main_layout = QVBoxLayout()
        grid = QGridLayout()
        grid.setSpacing(10)

        # Labels and text fields
        self.search_label = QLabel('검색어', self)
        self.search_input = QLineEdit(self)

        self.threading_label = QLabel('스레딩 인터넷수', self)
        self.threading_input = QLineEdit(self)

        self.pages_label1 = QLabel('검색페이지 수(쿠팡)', self)
        self.pages_input1 = QLineEdit(self)

        self.pages_label2 = QLabel('검색페이지 수(11번가)', self)
        self.pages_input2 = QLineEdit(self)

        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)

        self.progress_bar2 = QProgressBar(self)
        self.progress_bar2.setValue(0)

        # Execute button
        self.execute_button = QPushButton('실행', self)
        self.execute_button.clicked.connect(self.startcrawling)

        self.logBrowser = QPlainTextEditLogger(self)
        logging.getLogger().addHandler(self.logBrowser)
        logging.getLogger().setLevel(logging.INFO)

        # Adding widgets to the grid
        grid.addWidget(self.search_label, 1, 0)
        grid.addWidget(self.search_input, 1, 1)
        
        grid.addWidget(self.threading_label, 2, 0)
        grid.addWidget(self.threading_input, 2, 1)
        
        grid.addWidget(self.pages_label1, 3, 0)
        grid.addWidget(self.pages_input1, 3, 1)

        grid.addWidget(self.pages_label2, 4, 0)
        grid.addWidget(self.pages_input2, 4, 1)
        
        grid.addWidget(self.progress_bar, 6, 0, 1, 2)
        grid.addWidget(self.progress_bar2, 7, 0, 1, 2)
        
        grid.addWidget(self.execute_button, 5, 1)
        grid.addWidget(self.logBrowser.widget)
        
        self.setLayout(grid)

        self.setGeometry(300, 300, 400, 200)
        self.show()
        self.isdebug = False
        logging.info(f'프로그램이 정상적으로 실행되었습니다.')
    
    def startcrawling(self):
        try:
            search_input = self.search_input.text() 
            threading_input = self.threading_input.text()
            pages_input1 = self.pages_input1.text()
            pages_input2 = self.pages_input2.text()

            logging.info(f'프로그램 개시')
            self.progress_bar.setValue(0)
            self.crawling_thread = crawling(self.isdebug,
                                                    search_input,
                                                    threading_input,
                                                    pages_input1,
                                                    pages_input2
                                                    )
            self.crawling_thread.moveToThread(self.thread)
            self.crawling_thread.ReturnError.connect(self.ShowError)
            self.crawling_thread.returnMaxPb.connect(self.setMaxpb)
            self.crawling_thread.returnPb.connect(self.progress_bar.setValue)
            self.crawling_thread.returnPb2.connect(self.progress_bar2.setValue)
            self.crawling_thread.returnWarning.connect(self.showlog)
            self.thread.started.connect(self.crawling_thread.run)
            self.thread.start()

        except Exception as e:
            logging.info(f'Error during Conversion: {str(e)}')

    def showlog(self,str):
        logging.warning(f'{str}')

    def ShowError(self, str):
        logging.warning(f'PGM ERROR - {str}')
        self.thread.quit()
        self.thread.wait()
        self.progress_bar.setValue(0)
        self.progress_bar2.setValue(0)
        self.Conversion_thread = None

    def setMaxpb(self,maxPb):
        self.progress_bar.setRange(0,maxPb)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())
