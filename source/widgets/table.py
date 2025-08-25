from PIL import (
    Image, ImageDraw
)

from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QPushButton, QFileDialog,
    QDialog, QSizePolicy, QAbstractItemView
)

from PySide6.QtGui import (
    QPixmap, QImage
)

from PySide6.QtCore import (
    Qt
)

from source.internal.project import *
from source.widgets.drawing import DrawingWidget
from source.widgets.drawing import BigDrawingDialog
from source.widgets.duration import DurationWidget


class StoryboardTable(QTableWidget):
    def __init__(self, page_number=1, fps=DEFAULT_FPS, start_number=1, parent=None):
        super(StoryboardTable, self).__init__(ROWS_PER_PAGE, COLS, parent)
        
        self.page_number = page_number
        self.fps = fps
        self.start_number = start_number
        self.duration_widgets = []
        self.uploaded_images = [None] * ROWS_PER_PAGE
        self.draw_widgets = [None] * ROWS_PER_PAGE  # Store drawing widgets if in draw mode
        self.mode = "upload"  # def

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setEditTriggers(QAbstractItemView.AllEditTriggers)
        self.setHorizontalHeaderLabels(["#", "Storyboard", "Description", "Duration"])
        self.verticalHeader().setVisible(False)

        for row in range(ROWS_PER_PAGE):
            self.setItem(row, 0, self.create_number_item(self.start_number + row))
            self._add_upload_button(row)
            self._add_description_placeholder(row)
            self._add_duration_widget(row)

    def create_number_item(self, num):
        item = QTableWidgetItem(str(num))
        item.setFlags(Qt.ItemIsEnabled)
        item.setTextAlignment(Qt.AlignCenter)
        return item
    
    def update_geometry(self):
        total_width = self.viewport().width() or 800  # fallback if zero
        total_height = self.viewport().height() or 600

        margin_width = 20
        margin_height = 40

        total_width = max(0, total_width - margin_width)
        total_height = max(0, total_height - margin_height)

        row_height = total_height // ROWS_PER_PAGE
        for row in range(ROWS_PER_PAGE):
            self.setRowHeight(row, row_height)

        col1_width = int(total_width * 0.07)
        storyboard_width = int((16 / 9) * row_height)

        if storyboard_width > total_width - col1_width:
            storyboard_width = total_width - col1_width

        rest_width = total_width - (col1_width + storyboard_width)
        col3_width = int(rest_width * 0.7)
        col4_width = rest_width - col3_width

        self.setColumnWidth(0, col1_width)
        self.setColumnWidth(1, storyboard_width)
        self.setColumnWidth(2, col3_width)
        self.setColumnWidth(3, col4_width)

        # Resize drawing widgets if any
        for dw in self.draw_widgets:
            if dw:
                dw.setFixedSize(storyboard_width, row_height)

    def create_fixed_size_button(self, text=None, pixmap=None, row=None):
        btn = QPushButton()
        btn.setProperty("row", row)
        btn.setFlat(True)
        btn.setCheckable(False)  # 🔹 Make sure it's not a toggle button
        btn.setDown(False)     
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        if pixmap:
            btn.setIcon(pixmap)
            btn.setIconSize(pixmap.size())
            btn.setText("")
        else:
            btn.setText("Upload Image")
        btn.clicked.connect(self.handle_upload_clicked)
        return btn

    def _add_upload_button(self, row):
        btn = self.create_fixed_size_button(text="Upload Image", row=row)
        cell_width = 150
        cell_height =  85
        btn.setFixedSize(cell_width, cell_height)
        self.setCellWidget(row, 1, btn)

    def _add_description_placeholder(self, row):
        item = QTableWidgetItem(" ")
        self.setItem(row, 2, item)

    def _add_duration_widget(self, row):
        dur_widget = DurationWidget(fps=self.fps)
        dur_widget.on_value_changed(self.notify_parent_to_update_total)
        cell_width = self.columnWidth(3) or 80
        cell_height = self.rowHeight(row) or 50
        dur_widget.setFixedSize(cell_width, cell_height)
        self.setCellWidget(row, 3, dur_widget)
        self.duration_widgets.append(dur_widget)

    def notify_parent_to_update_total(self):
        parent = self.parent()
        while parent:
            if hasattr(parent, "update_totals_for_page"):
                parent.update_totals_for_page(self)
                break
            parent = parent.parent()

    def update_page_total_duration(self):
        total_seconds = 0
        total_frames = 0
        for dur_widget in self.duration_widgets:
            s, f = dur_widget.get_duration()
            total_seconds += s
            total_frames += f

        extra_seconds = total_frames // self.fps
        total_seconds += extra_seconds
        total_frames = total_frames % self.fps
        return total_seconds, total_frames

    def handle_upload_clicked(self):
        button = self.sender()
        if button:
            button.setDown(False)  # 🔹 reset visual press

        if not button:
            return
        row = button.property("row")
        if row is None:
            return

        if self.mode != "upload":
            # in draw mode, do nothing on upload button clicks
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Storyboard Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if not file_path:
            return

        pil_img = Image.open(file_path).convert("RGBA")
        self.uploaded_images[row] = pil_img

        cell_width = self.columnWidth(1) or 150
        cell_height = self.rowHeight(row) or 50
        qt_pixmap = self.pil_to_qpixmap_scaled(pil_img, cell_width, cell_height)

        img_btn = self.create_fixed_size_button(pixmap=qt_pixmap, row=row)
        img_btn.setFixedSize(cell_width, cell_height)
        img_btn.setToolTip(file_path)
        self.setCellWidget(row, 1, img_btn)

        # Clear draw widget if any
        if self.draw_widgets[row]:
            self.draw_widgets[row].deleteLater()
            self.draw_widgets[row] = None

    def pil_to_qpixmap_scaled(self, pil_img, width, height):
        img_ratio = pil_img.width / pil_img.height
        target_ratio = width / height

        if img_ratio > target_ratio:
            new_width = width
            new_height = int(width / img_ratio)
        else:
            new_height = height
            new_width = int(height * img_ratio)

        resized_img = pil_img.resize((new_width, new_height), Image.LANCZOS)
        data = resized_img.tobytes("raw", "RGBA")
        qimg = QImage(data, resized_img.width, resized_img.height, QImage.Format_RGBA8888)
        return QPixmap.fromImage(qimg)

    def switch_to_draw_mode(self):
        self.mode = "draw"
        # Replace storyboard column widgets with DrawingWidgets or blank if none
        for row in range(ROWS_PER_PAGE):
            if self.draw_widgets[row] is None:
                dw = DrawingWidget(self.columnWidth(1), self.rowHeight(row))
                self.draw_widgets[row] = dw
            else:
                dw = self.draw_widgets[row]
                dw.setFixedSize(self.columnWidth(1), self.rowHeight(row))
            self.setCellWidget(row, 1, self.draw_widgets[row])
            self.uploaded_images[row] = None  # Clear uploaded images in draw mode

    def switch_to_upload_mode(self):
        self.mode = "upload"
        # Replace storyboard column widgets with upload buttons or uploaded image buttons
        for row in range(ROWS_PER_PAGE):
            if self.draw_widgets[row]:
                self.draw_widgets[row].deleteLater()
                self.draw_widgets[row] = None
            if self.uploaded_images[row]:
                pil_img = self.uploaded_images[row]
                cell_width = self.columnWidth(1) or 150
                cell_height = self.rowHeight(row) or 50
                qt_pixmap = self.pil_to_qpixmap_scaled(pil_img, cell_width, cell_height)
                img_btn = self.create_fixed_size_button(pixmap=qt_pixmap, row=row)
                img_btn.setFixedSize(cell_width, cell_height)
                self.setCellWidget(row, 1, img_btn)
            else:
                self._add_upload_button(row)

    def mousePressEvent(self, event):
        if self.mode != "draw":
            super().mousePressEvent(event)
            return

        pos = event.position().toPoint() if hasattr(event, 'position') else event.pos()
        index = self.indexAt(pos)
        if not index.isValid():
            super().mousePressEvent(event)
            return

        row = index.row()
        col = index.column()
        if col == 1 and 0 <= row < ROWS_PER_PAGE:
            # Load full-res image from uploaded_images, fallback to blank canvas
            current_img = self.uploaded_images[row]
            if current_img is None:
                current_img = Image.new("RGBA", (800, 450), (255, 255, 255, 255))

            dlg = BigDrawingDialog(
                pil_image=current_img,
                brush_color=self.draw_widgets[row].brush_color if self.draw_widgets[row] else (0, 0, 0, 255),
                brush_size=self.draw_widgets[row].brush_size if self.draw_widgets[row] else 5,
                eraser_mode=self.draw_widgets[row].eraser_mode if self.draw_widgets[row] else False,
                parent=self
            )
            if dlg.exec() == QDialog.Accepted:
                new_img = dlg.get_image()

                # Store full-res image for playback/export
                self.uploaded_images[row] = new_img

                # Create thumbnail sized to cell
                thumb_width = self.columnWidth(1)
                thumb_height = self.rowHeight(row)
                thumbnail_img = new_img.resize((thumb_width, thumb_height), Image.LANCZOS)

                # Update or create the draw widget thumbnail
                if self.draw_widgets[row]:
                    self.draw_widgets[row].image = thumbnail_img
                    self.draw_widgets[row].draw = ImageDraw.Draw(self.draw_widgets[row].image)
                    self.draw_widgets[row].update_pixmap()
                else:
                    dw = DrawingWidget(thumb_width, thumb_height)
                    dw.image = thumbnail_img
                    dw.draw = ImageDraw.Draw(dw.image)
                    dw.update_pixmap()
                    self.draw_widgets[row] = dw
                    self.setCellWidget(row, 1, dw)

                # Update draw widget image resized to widget size for thumbnail
                if self.draw_widgets[row]:
                    self.draw_widgets[row].image = new_img.resize(
                        (self.draw_widgets[row].width(), self.draw_widgets[row].height()),
                        Image.LANCZOS
                    )
                    self.draw_widgets[row].draw = ImageDraw.Draw(self.draw_widgets[row].image)
                    self.draw_widgets[row].update_pixmap()
                    # Store full res big image in uploaded_images for player
                    self.uploaded_images[row] = new_img
                else:
                    # Justincase
                    dw = DrawingWidget(self.columnWidth(1), self.rowHeight(row))
                    dw.image = new_img.resize(
                        (dw.width(), dw.height()), Image.LANCZOS)
                    dw.draw = ImageDraw.Draw(dw.image)
                    dw.update_pixmap()
                    self.draw_widgets[row] = dw
                    self.setCellWidget(row, 1, dw)
                    self.uploaded_images[row] = new_img
        else:
            super().mousePressEvent(event)

    def resizeEvent(self, event):
        total_width = self.viewport().width()
        total_height = self.viewport().height()

        margin_width = 20
        margin_height = 40

        total_width = max(0, total_width - margin_width)
        total_height = max(0, total_height - margin_height)

        row_height = total_height // ROWS_PER_PAGE
        for row in range(ROWS_PER_PAGE):
            self.setRowHeight(row, row_height)

        col1_width = int(total_width * 0.07)
        storyboard_width = int((16 / 9) * row_height)

        if storyboard_width > total_width - col1_width:
            storyboard_width = total_width - col1_width

        rest_width = total_width - (col1_width + storyboard_width)
        col3_width = int(rest_width * 0.7)
        col4_width = rest_width - col3_width

        self.setColumnWidth(0, col1_width)
        self.setColumnWidth(1, storyboard_width)
        self.setColumnWidth(2, col3_width)
        self.setColumnWidth(3, col4_width)

        # Resize drawing widgets if any
        for dw in self.draw_widgets:
            if dw:
                dw.setFixedSize(storyboard_width, row_height)

        super().resizeEvent(event)