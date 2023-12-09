from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QVBoxLayout,  QMessageBox,  QSlider
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon
from PyQt6 import QtWidgets, uic
import numpy as np
import pandas as pd
import sys
import pyqtgraph as pg
import qdarkstyle
import os
from scipy import signal
import librosa
import matplotlib
import sounddevice as sd
from functools import partial
import bisect


from imageViewPort import ImageViewport
from FTViewPort import FTViewPort
from mixer import ImageMixer


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.init_ui()

    def init_ui(self):
        # Load the UI Page
        self.ui = uic.loadUi('Mainwindow.ui', self)
        self.setWindowTitle("FT Mixer")
        self.image_ports = []
        self.components_ports = []
        self.components = {"0": '', "1": '', "2": '', "3": ''}
        # mixer and its connection line
        self.mixer = ImageMixer(self)
        self.ui.mixxer.clicked.connect(self.mixer.mix_images)

        self.load_ui_elements()
        self.showFullScreen()
        self.ui.keyPressEvent = self.keyPressEvent

    def keyPressEvent(self, event):
        # Handle key events, for example, pressing ESC to exit full screen
        if event.key() == Qt.Key.Key_Escape:
            self.showNormal()  # Show the window in normal size
        else:
            super().keyPressEvent(event)

    def load_ui_elements(self):
        """
        Load UI elements.

        This function is responsible for loading the UI elements of the application. It initializes and configures various UI components 
        such as view ports, combo boxes, sliders, and connects them to the appropriate event handlers.

        """
        # List of original UI view ports
        ui_view_ports = [self.ui.original1, self.ui.original2,
                         self.ui.original3, self.ui.original4]

        self.ui_view_ports_comp = [
            self.ui.component_image1, self.ui.component_image2, self.ui.component_image3, self.ui.component_image4]
        # List of combo boxes for UI
        self.ui_image_combo_boxes = [
            self.ui.combo1, self.ui.combo2, self.ui.combo3, self.ui.combo4]

        # List of combo boxes for mixing UI
        self.ui_mixing_combo_boxes = [
            self.ui.combo11, self.ui.combo12, self.ui.combo13, self.ui.combo14]

        # Create image viewports and bind browse_image function to the event
        self.image_ports.extend([
            self.create_image_viewport(
                ui_view_ports[i], lambda event, index=i: self.browse_image(event, index))
            for i in range(4)
        ])

        self.components_ports.extend([
            self.create_FT_viewport(
                self.ui_view_ports_comp[i], lambda event, index=i: self.mixer.collect_chunks(event, index))
            for i in range(4)
        ])

        self.ui_vertical_sliders = [
            self.ui.Slider_weight1, self.ui.Slider_weight2, self.ui.Slider_weight3, self.ui.Slider_weight4]

        # Add items to combo boxes for mixing UI
        for combo_box in self.ui_mixing_combo_boxes:
            combo_box.addItems([f'image{i+1}' for i in range(4)])

        for i, combo_box in enumerate(self.ui_image_combo_boxes):
            self.components_ports[i].combo_box = combo_box
            combo_box.addItems(
                ["FT Magnitude", "FT Phase", "FT Real", "FT Imaginary"])
            combo_box.setCurrentIndex(i)
            combo_box.currentIndexChanged.connect(
                self.components_ports[i].handle_image_combo_boxes_selection)

        # List of brightness sliders
        self.ui_brightness_sliders = [
            getattr(self.ui, f"brightnessSlider{i+1}") for i in range(4)]

        # List of contrast sliders
        self.ui_contrast_sliders = [
            getattr(self.ui, f"contrastSlider{i+1}") for i in range(4)]

        # Set minimum, maximum, and initial value for brightness and contrast sliders
        for image_ind, slider_pairs in enumerate(zip(self.ui_brightness_sliders, self.ui_contrast_sliders)):
            self.image_ports[image_ind].slider_pairs = slider_pairs
            for slider in slider_pairs:
                slider.setMinimum(-255)
                slider.setMaximum(255)
                slider.setValue(0)
                slider.valueChanged.connect(
                    self.image_ports[image_ind].update_slider)

    def browse_image(self, event, index: int):
        """
        Browse for an image file and set it for the ImageViewport at the specified index.

        Args:
            event: The event that triggered the image browsing.
            index: The index of the ImageViewport to set the image for.
        """
        file_filter = "Raw Data (*.png *.jpg *.jpeg *.jfif)"
        image_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            None, 'Open Signal File', './', filter=file_filter)

        if image_path and 0 <= index < len(self.image_ports):
            image_port = self.image_ports[index]
            image_port.update_image_parameters(index, image_path)
            self.components_ports[index].viewport_FT_ind = index
            self.components_ports[index].update_FT_components()
            # print(
            #     f"the size of the image before resizing{np.array(image_port.original_img).shape}")
            # print(
            #     f"the size of the image after resizing{np.array( image_port.resized_img).shape}")

    def create_image_viewport(self, parent, mouse_double_click_event_handler):
        """
        Creates an image viewport and adds it to the specified parent widget.

        Args:
            parent: The parent widget to which the image viewport will be added.
            mouse_double_click_event_handler: The event handler function to be called when a mouse double-click event occurs on the image viewport.

        Returns:
            The created image viewport.

        """
        image_port = ImageViewport(self)
        image_layout = QVBoxLayout(parent)
        image_layout.addWidget(image_port)
        image_port.mouseDoubleClickEvent = mouse_double_click_event_handler
        return image_port

    def create_FT_viewport(self, parent, mouse_double_click_event_handler):
        """
        Creates an FT viewport and adds it to the specified parent widget.

        Args:
            parent: The parent widget to which the image viewport will be added.
            mouse_double_click_event_handler: The event handler function to be called when a mouse double-click event occurs on the image viewport.

        Returns:
            The created FT viewport.

        """
        FT_port = FTViewPort(self)
        FT_layout = QVBoxLayout(parent)
        FT_layout.addWidget(FT_port)
        FT_port.mouseDoubleClickEvent = mouse_double_click_event_handler
        return FT_port


def main():
    app = QtWidgets.QApplication([])
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt6())
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
