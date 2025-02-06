import sys
import os
from PyQt5.QtWidgets import (QApplication, QDialog, QMainWindow, QShortcut, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, 
                             QPushButton, QComboBox, QCheckBox, QSplitter, QLineEdit, QToolBar, QAction, 
                             QFileDialog, QPlainTextEdit, QToolTip, QFrame)
from PyQt5.QtGui import QColor, QKeySequence, QPainter, QTextCharFormat, QFont, QSyntaxHighlighter, QTextCursor, QPalette, QIcon, QTextFormat, QMouseEvent
from PyQt5.QtCore import QRect, QSize, Qt, QRegExp, QThread, pyqtSignal, QRunnable, QObject, QThreadPool, QPoint
from transformers import AutoTokenizer
import random

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.editor.lineNumberAreaPaintEvent(event)

class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lineNumberArea = LineNumberArea(self)
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        self.updateLineNumberAreaWidth(0)

    def lineNumberAreaWidth(self):
        digits = 1
        max_value = max(1, self.blockCount())
        while max_value >= 10:
            max_value /= 10
            digits += 1
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), Qt.lightGray)
        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.setPen(Qt.black)
                painter.drawText(0, int(top), self.lineNumberArea.width(), self.fontMetrics().height(),
                                Qt.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            blockNumber += 1

    def highlightCurrentLine(self):
        extraSelections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            lineColor = QColor(Qt.yellow).lighter(160)
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
        self.setExtraSelections(extraSelections)

class CustomTitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(32)
        self.setup_ui()
        
        # Initial position for window movement
        self.start = QPoint(0, 0)
        self.pressing = False

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title label
        self.title_label = QLabel("Tokenz Machine")
        self.title_label.setStyleSheet("""
            color: #E5E9F0;
            font-size: 14px;
            font-weight: bold;
            padding-left: 10px;
        """)
        
        # Window controls
        btn_size = 46
        self.minimize_btn = QPushButton("−")
        self.maximize_btn = QPushButton("□")
        self.close_btn = QPushButton("×")
        
        for btn in (self.minimize_btn, self.maximize_btn, self.close_btn):
            btn.setFixedSize(btn_size, 32)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                    color: #E5E9F0;
                    font-size: 16px;
                }
                QPushButton:hover {
                    background-color: #4C566A;
                }
            """)
        
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #E5E9F0;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #BF616A;
            }
        """)
        
        # Connect buttons
        self.minimize_btn.clicked.connect(self.parent.showMinimized)
        self.maximize_btn.clicked.connect(self.toggle_maximize)
        self.close_btn.clicked.connect(self.parent.close)
        
        # Add widgets to layout
        layout.addWidget(self.title_label)
        layout.addStretch()
        layout.addWidget(self.minimize_btn)
        layout.addWidget(self.maximize_btn)
        layout.addWidget(self.close_btn)
        
        self.setStyleSheet("""
            CustomTitleBar {
                background-color: #2E3440;
            }
        """)

    def toggle_maximize(self):
        if self.parent.isMaximized():
            self.parent.showNormal()
        else:
            self.parent.showMaximized()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start = self.mapToGlobal(event.pos())
            self.pressing = True

    def mouseMoveEvent(self, event):
        if self.pressing:
            if self.parent.isMaximized():
                self.parent.showNormal()
            
            self.end = self.mapToGlobal(event.pos())
            movement = self.end - self.start
            
            self.parent.setGeometry(
                self.parent.pos().x() + movement.x(),
                self.parent.pos().y() + movement.y(),
                self.parent.width(),
                self.parent.height()
            )
            self.start = self.end

    def mouseReleaseEvent(self, event):
        self.pressing = False

    def mouseDoubleClickEvent(self, event):
        self.toggle_maximize()

class TokenizationWorker(QRunnable):
    class Signals(QObject):
        result = pyqtSignal(object)
        progress = pyqtSignal(int)

    def __init__(self, tokenizer, text, max_length=1024):
        super().__init__()
        self.tokenizer = tokenizer
        self.text = text
        self.max_length = max_length
        self.signals = self.Signals()

    def run(self):
        chunks = [self.text[i:i+self.max_length] for i in range(0, len(self.text), self.max_length)]
        total_tokens = []
        total_offsets = []
        
        for i, chunk in enumerate(chunks):
            tokens = self.tokenizer(chunk, add_special_tokens=True, return_offsets_mapping=True)
            total_tokens.extend(tokens["input_ids"])
            
            # Adjust offsets for chunks after the first one
            if i > 0:
                offset_adjustment = i * self.max_length
                adjusted_offsets = [(start + offset_adjustment, end + offset_adjustment) for start, end in tokens["offset_mapping"]]
                total_offsets.extend(adjusted_offsets)
            else:
                total_offsets.extend(tokens["offset_mapping"])
            
            self.signals.progress.emit((i + 1) * 100 // len(chunks))

        self.signals.result.emit({"input_ids": total_tokens, "offset_mapping": total_offsets})

class CustomToolBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Create toolbar buttons
        self.tokenize_btn = QPushButton("Tokenize")
        self.clear_btn = QPushButton("Clear")
        self.save_btn = QPushButton("Save")
        self.open_btn = QPushButton("Open")
        self.find_btn = QPushButton("Find")

        # Add buttons to layout
        for btn in [self.tokenize_btn, self.clear_btn, self.save_btn, self.open_btn, self.find_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                    color: #E5E9F0;
                    padding: 6px 12px;
                    margin: 0;
                    border-radius: 0;
                }
                QPushButton:hover {
                    background-color: #4C566A;
                }
            """)
            layout.addWidget(btn)
        
        layout.addStretch()
        
        self.setStyleSheet("""
            CustomToolBar {
                background-color: #3B4252;
            }
        """)
class CustomToolBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Create toolbar buttons
        self.tokenize_btn = QPushButton("Tokenize")
        self.clear_btn = QPushButton("Clear")
        self.save_btn = QPushButton("Save")
        self.open_btn = QPushButton("Open")
        self.find_btn = QPushButton("Find")

        # Add buttons to layout
        for btn in [self.tokenize_btn, self.clear_btn, self.save_btn, self.open_btn, self.find_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                    color: #E5E9F0;
                    padding: 6px 12px;
                    margin: 0;
                    border-radius: 0;
                }
                QPushButton:hover {
                    background-color: #4C566A;
                }
            """)
            layout.addWidget(btn)
        
        layout.addStretch()
        
        self.setStyleSheet("""
            CustomToolBar {
                background-color: #3B4252;
            }
        """)

class TokenzMachine(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tokenz Machine")
        self.setGeometry(100, 100, 1200, 800)
        # Remove toolbar area and set window flags
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)
        self.setup_ui_style()

        self.model_list = [
            "gpt2", "bert-base-uncased", "roberta-base", "t5-small", "distilbert-base-uncased"
        ]

        self.current_model = self.model_list[0]
        self.tokenizer = AutoTokenizer.from_pretrained(self.current_model)

        self.color_gradients = {
            "Nord Aurora": ["#BF616A", "#D08770", "#EBCB8B", "#A3BE8C", "#B48EAD"],
            "Nord Frost": ["#8FBCBB", "#88C0D0", "#81A1C1", "#5E81AC"],
            "Ocean": ["#0077BE", "#009DC4", "#00C5CD", "#48D1CC", "#20B2AA"],
            "Forest": ["#228B22", "#32CD32", "#90EE90", "#98FB98", "#3CB371"],
            "Sunset": ["#FF7F50", "#FF6B6B", "#FF4500", "#FF8C00", "#FFA500"],
            "Berry": ["#8B0000", "#B22222", "#DC143C", "#FF69B4", "#DB7093"],
            "Desert": ["#DEB887", "#D2B48C", "#F4A460", "#DAA520", "#CD853F"],
            "Galaxy": ["#483D8B", "#4B0082", "#800080", "#8A2BE2", "#9370DB"],
            "Autumn": ["#8B4513", "#CD853F", "#DEB887", "#D2691E", "#A0522D"],
            "Spring": ["#98FB98", "#90EE90", "#3CB371", "#2E8B57", "#228B22"],
            "Winter": ["#B0C4DE", "#B0E0E6", "#87CEEB", "#87CEFA", "#00BFFF"],
            "Summer": ["#FFD700", "#FFA500", "#FF8C00", "#FF7F50", "#FF6347"],
            "Retro": ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEEAD"],
            "Candy": ["#FF69B4", "#FFB6C1", "#FFC0CB", "#FF1493", "#C71585"],
            "Earth": ["#8B4513", "#A0522D", "#6B8E23", "#556B2F", "#2F4F4F"],
            "Jewel": ["#9400D3", "#4B0082", "#0000CD", "#00008B", "#191970"],
            "Pastel": ["#FFB3BA", "#FFDFBA", "#FFFFBA", "#BAFFC9", "#BAE1FF"],
            "Neon": ["#FF00FF", "#00FFFF", "#FF00FF", "#00FF00", "#FFFF00"],
            "Monochrome": ["#000000", "#333333", "#666666", "#999999", "#CCCCCC"],
            "Rainbow": ["#FF0000", "#FF7F00", "#FFFF00", "#00FF00", "#0000FF", "#4B0082", "#8F00FF"],
            "Cyber": ["#00FF00", "#00FFFF", "#FF00FF", "#FF0000", "#0000FF"],
            "Nordic": ["#D8DEE9", "#E5E9F0", "#ECEFF4", "#81A1C1", "#88C0D0"],
            "Ice": ["#F0F8FF", "#E0FFFF", "#B0E0E6", "#B0C4DE", "#87CEEB"],
            "Fire": ["#8B0000", "#B22222", "#CD5C5C", "#FF4500", "#FF6347"],
            "Deep Sea": ["#000080", "#00008B", "#0000CD", "#0000FF", "#1E90FF"],
            "Bamboo": ["#006400", "#228B22", "#32CD32", "#90EE90", "#98FB98"],
            "Dusk": ["#4B0082", "#483D8B", "#6A5ACD", "#7B68EE", "#8A2BE2"],
            "Dawn": ["#FF69B4", "#DDA0DD", "#EE82EE", "#DA70D6", "#BA55D3"],
            "Randomize": [],
        }




        self.model_list = [
            "gpt2", "bert-base-uncased", "roberta-base", "t5-small", "distilbert-base-uncased"
        ]



        self.init_ui()
        self.setup_shortcuts()
        self.setup_token_hover()

        self.threadpool = QThreadPool()
        self.setup_ui_style()
        
    def setup_ui_style(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #2E3440;
                color: #D8DEE9;
            }
            QTextEdit, QLineEdit {
                background-color: #3B4252;
                color: #E5E9F0;
                border: 1px solid #4C566A;
                border-radius: 5px;
                padding: 5px;
            }
            QComboBox {
                background-color: #3B4252;
                color: #E5E9F0;
                border: 1px solid #4C566A;
                border-radius: 5px;
                padding: 5px;
                padding-right: 20px;
            }
            QComboBox::drop-down {
                border: none;
                border-left: 1px solid #4C566A;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png);
                width: 16px;
                height: 16px;
            }
            QComboBox QAbstractItemView {
                background-color: #3B4252;
                color: #E5E9F0;
                border: 1px solid #4C566A;
                selection-background-color: #4C566A;
            }
            QLabel {
                color: #E5E9F0;
            }
            QPushButton {
                background-color: #5E81AC;
                color: #ECEFF4;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #81A1C1;
            }
            QCheckBox {
                color: #E5E9F0;
            }
            QSplitter::handle {
                background-color: #4C566A;
            }
            QToolBar {
                background-color: #3B4252;
                border: none;
                spacing: 3px;
            }
            QToolButton {
                background-color: transparent;
                border: none;
                padding: 3px;
                border-radius: 3px;
            }
            QToolButton:hover {
                background-color: #4C566A;
            }
        """)

    def init_ui(self):
        # Main widget setup
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create and add our custom title bar
        self.title_bar = CustomTitleBar(self)
        main_layout.addWidget(self.title_bar)

        # Create and add our custom toolbar AFTER the title bar
        self.toolbar = CustomToolBar()
        self.toolbar.tokenize_btn.clicked.connect(self.calculate_and_visualize_tokens)
        self.toolbar.clear_btn.clicked.connect(self.clear_text)
        self.toolbar.save_btn.clicked.connect(self.save_file)
        self.toolbar.open_btn.clicked.connect(self.open_file)
        self.toolbar.find_btn.clicked.connect(self.show_find_dialog)
        main_layout.addWidget(self.toolbar)

        # Content area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(6, 6, 6, 6)
        content_layout.setSpacing(4)
        main_layout.addWidget(content_widget)

        # Controls area (top) - more compact
        controls_widget = QWidget()
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(2, 2, 2, 2)
        controls_layout.setSpacing(8)
        
        # Model selection - more compact
        model_layout = QHBoxLayout()
        model_layout.setSpacing(4)
        model_label = QLabel("Model:")
        model_label.setStyleSheet("font-weight: bold;")
        self.model_combo = QComboBox()
        self.model_combo.addItems(self.model_list)
        self.model_combo.currentIndexChanged.connect(self.update_tokenizer)
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combo)
        controls_layout.addLayout(model_layout)

        # Gradient selection - more compact
        gradient_layout = QHBoxLayout()
        gradient_layout.setSpacing(4)
        gradient_label = QLabel("Color Gradient:")
        gradient_label.setStyleSheet("font-weight: bold;")
        self.gradient_combo = QComboBox()
        self.gradient_combo.addItems(self.color_gradients.keys())
        gradient_layout.addWidget(gradient_label)
        gradient_layout.addWidget(self.gradient_combo)
        controls_layout.addLayout(gradient_layout)

        # Color checkbox - enabled by default
        self.color_checkbox = QCheckBox("Enable Coloring")
        self.color_checkbox.setStyleSheet("font-weight: bold;")
        self.color_checkbox.setChecked(True)  # Enable coloring by default
        controls_layout.addWidget(self.color_checkbox)
        controls_layout.addStretch()
        content_layout.addWidget(controls_widget)

        # Main content area (side-by-side with minimal spacing)
        split_widget = QSplitter(Qt.Horizontal)
        split_widget.setHandleWidth(1)  # Minimal splitter handle
        content_layout.addWidget(split_widget)
        content_layout.setStretch(1, 1)  # Give more stretch to the content area

        # Left side (input)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(2, 2, 2, 2)
        left_layout.setSpacing(2)
        input_label = QLabel("Input Text:")
        input_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        left_layout.addWidget(input_label)
        
        self.text_input = CodeEditor()
        self.text_input.setStyleSheet("""
            font-family: 'Fira Code', 'Consolas', monospace;
            font-size: 14px;
            line-height: 1.5;
            min-height: 500px;  /* Ensure minimum height */
        """)
        left_layout.addWidget(self.text_input)
        left_layout.setStretch(1, 1)  # Give more stretch to the input area
        split_widget.addWidget(left_widget)

        # Right side (visualization)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(2, 2, 2, 2)
        right_layout.setSpacing(2)
        vis_label = QLabel("Token Visualization:")
        vis_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        right_layout.addWidget(vis_label)
        
        self.token_area = QTextEdit()
        self.token_area.setReadOnly(True)
        self.token_area.setStyleSheet("""
            font-family: 'Fira Code', 'Consolas', monospace;
            font-size: 14px;
            line-height: 1.5;
            min-height: 500px;  /* Ensure minimum height */
        """)
        right_layout.addWidget(self.token_area)
        right_layout.setStretch(1, 1)  # Give more stretch to the visualization area
        split_widget.addWidget(right_widget)

        # Status area (bottom)
        self.result_label = QLabel("Token Count: 0 | Character Count: 0 | Word Count: 0")
        self.result_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 5px;")
        content_layout.addWidget(self.result_label)

        # Set initial splitter sizes
        split_widget.setSizes([600, 600])

    def create_toolbar(self):
        toolbar = QToolBar()
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #3B4252;
                border: none;
                padding: 2px;
            }
            QToolBar QToolButton {
                background-color: transparent;
                border: none;
                padding: 6px;
                margin: 0;
                border-radius: 0;
            }
            QToolBar QToolButton:hover {
                background-color: #4C566A;
            }
        """)
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        # Add actions to the toolbar
        tokenize_action = QAction(QIcon.fromTheme("edit-find"), "Tokenize", self)
        tokenize_action.triggered.connect(self.calculate_and_visualize_tokens)
        toolbar.addAction(tokenize_action)

        clear_action = QAction(QIcon.fromTheme("edit-clear"), "Clear", self)
        clear_action.triggered.connect(self.clear_text)
        toolbar.addAction(clear_action)

        toolbar.addSeparator()

        save_action = QAction(QIcon.fromTheme("document-save"), "Save", self)
        save_action.triggered.connect(self.save_file)
        toolbar.addAction(save_action)

        open_action = QAction(QIcon.fromTheme("document-open"), "Open", self)
        open_action.triggered.connect(self.open_file)
        toolbar.addAction(open_action)

        toolbar.addSeparator()

        find_action = QAction(QIcon.fromTheme("edit-find"), "Find", self)
        find_action.triggered.connect(self.show_find_dialog)
        toolbar.addAction(find_action)

    def setup_shortcuts(self):
        # Tokenize
        tokenize_shortcut = QShortcut(QKeySequence("Ctrl+T"), self)
        tokenize_shortcut.activated.connect(self.calculate_and_visualize_tokens)

        # Save
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.save_file)

        # Open
        open_shortcut = QShortcut(QKeySequence("Ctrl+O"), self)
        open_shortcut.activated.connect(self.open_file)

        # Find
        find_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        find_shortcut.activated.connect(self.show_find_dialog)

        # Clear
        clear_shortcut = QShortcut(QKeySequence("Ctrl+L"), self)
        clear_shortcut.activated.connect(self.clear_text)

    def update_tokenizer(self):
        self.current_model = self.model_combo.currentText()
        self.tokenizer = AutoTokenizer.from_pretrained(self.current_model)
        print(f"Switched to {self.current_model} tokenizer")
        self.calculate_and_visualize_tokens()

    def get_random_color(self):
        return QColor(random.randint(128, 255), random.randint(128, 255), random.randint(128, 255))

    def get_color_for_token(self, index, token_count):
        selected_gradient = self.gradient_combo.currentText()
        gradient = self.color_gradients.get(selected_gradient, [])

        if selected_gradient == "Randomize":
            random.seed(index)
            return self.get_random_color()

        if gradient:
            num_colors = len(gradient)
            if num_colors == 0:
                return QColor(255, 255, 255)

            color = QColor(gradient[index % num_colors])
            return color

        return QColor(255, 255, 255)

    def calculate_and_visualize_tokens(self):
        input_text = self.text_input.toPlainText()
        
        worker = TokenizationWorker(self.tokenizer, input_text)
        worker.signals.result.connect(self.handle_tokenization_result)
        worker.signals.progress.connect(self.update_progress)
        self.threadpool.start(worker)
        
    def update_progress(self, value):
        self.statusBar().showMessage(f"Tokenization progress: {value}%")

    def handle_tokenization_result(self, tokens):
        self.token_ids = tokens["input_ids"]
        self.offsets = tokens["offset_mapping"]
        token_count = len(self.token_ids)
        
        input_text = self.text_input.toPlainText()
        char_count = len(input_text)
        word_count = len(input_text.split())

        self.result_label.setText(f"Token Count: {token_count} | Character Count: {char_count} | Word Count: {word_count}")

        self.visualize_tokens(input_text, self.offsets)
        
    def visualize_tokens(self, input_text, offsets):
        self.token_area.clear()
        cursor = self.token_area.textCursor()
        for i, (start, end) in enumerate(offsets):
            token_text = input_text[start:end]
            color = self.get_color_for_token(i, len(self.token_ids))
            format = QTextCharFormat()
            format.setBackground(color)
            if self.color_checkbox.isChecked():
                cursor.insertText(token_text, format)
            else:
                cursor.insertText(token_text)
            cursor.insertText(" ")  # Add space between tokens for readability

    def clear_text(self):
        self.text_input.clear()
        self.token_area.clear()
        self.result_label.setText("Token Count: 0 | Character Count: 0 | Word Count: 0")

    def save_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Text Files (*.txt);;All Files (*)")
        if file_path:
            with open(file_path, 'w') as file:
                file.write(self.text_input.toPlainText())

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Text Files (*.txt);;All Files (*)")
        if file_path:
            with open(file_path, 'r') as file:
                self.text_input.setPlainText(file.read())

    def show_find_dialog(self):
        find_dialog = QDialog(self)
        find_dialog.setWindowTitle("Find and Replace")
        layout = QVBoxLayout(find_dialog)

        find_label = QLabel("Find:")
        self.find_input = QLineEdit()
        layout.addWidget(find_label)
        layout.addWidget(self.find_input)

        replace_label = QLabel("Replace with:")
        self.replace_input = QLineEdit()
        layout.addWidget(replace_label)
        layout.addWidget(self.replace_input)

        find_button = QPushButton("Find")
        find_button.clicked.connect(self.find_text)
        layout.addWidget(find_button)

        replace_button = QPushButton("Replace")
        replace_button.clicked.connect(self.replace_text)
        layout.addWidget(replace_button)

        replace_all_button = QPushButton("Replace All")
        replace_all_button.clicked.connect(self.replace_all_text)
        layout.addWidget(replace_all_button)

        find_dialog.setLayout(layout)
        find_dialog.exec_()

    def find_text(self):
        text = self.find_input.text()
        if text:
            cursor = self.text_input.document().find(text)
            if not cursor.isNull():
                self.text_input.setTextCursor(cursor)
            else:
                self.statusBar().showMessage("Text not found", 2000)

    def replace_text(self):
        find_text = self.find_input.text()
        replace_text = self.replace_input.text()
        if find_text and replace_text:
            cursor = self.text_input.textCursor()
            if cursor.hasSelection() and cursor.selectedText() == find_text:
                cursor.insertText(replace_text)
            self.find_text()

    def replace_all_text(self):
        find_text = self.find_input.text()
        replace_text = self.replace_input.text()
        if find_text and replace_text:
            cursor = self.text_input.textCursor()
            cursor.beginEditBlock()
            while True:
                cursor = self.text_input.document().find(find_text, cursor)
                if cursor.isNull():
                    break
                cursor.insertText(replace_text)
            cursor.endEditBlock()

    def setup_token_hover(self):
        self.token_area.setMouseTracking(True)
        self.token_area.mouseMoveEvent = self.token_hover_event

    def token_hover_event(self, event):
        cursor = self.token_area.cursorForPosition(event.pos())
        cursor.select(QTextCursor.WordUnderCursor)
        word = cursor.selectedText()

        if word:
            token_info = self.get_token_info(word)
            QToolTip.showText(self.token_area.mapToGlobal(event.pos()), token_info)
        else:
            QToolTip.hideText()

    def get_token_info(self, word):
        try:
            token_id = self.tokenizer.convert_tokens_to_ids(word)
            return f"Token: {word}\nID: {token_id}"
        except:
            return "Token information not available"

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TokenzMachine()
    window.show()
    sys.exit(app.exec_())