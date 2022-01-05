import sys
import threading

from kivy.app import App
from kivy.clock import mainthread
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.utils import platform

from datetime import date
from datetime import time
from datetime import datetime

if platform == 'android':
    from usb4a import usb
    from usbserial4a import serial4a
else:
    from serial.tools import list_ports
    from serial import Serial


class MainApp(App):
    def __init__(self, *args, **kwargs):
        self.uiDict = {}
        self.device_name_list = []
        self.serial_port = None
        self.read_thread = None
        self.port_thread_lock = threading.Lock()
        self.text_btn = ""
        self.sol_text = ""
        super(MainApp, self).__init__(*args, **kwargs)
        self.init_com()

    # Create view of App from Design.kv
    def build(self):
        return Builder.load_file('Design.kv')

    # Active button 1 display screen_view
    def on_btn_screen_1(self):
        self.uiDict['sm'].current = 'screen_view'

    # Active button 2 display screen_send
    def on_btn_screen_2(self):
        self.uiDict['sm'].current = 'screen_send'
    # Active button 3 display screen_settings
    def on_btn_screen_3(self):
        self.uiDict['sm'].current = 'screen_settings'

    # Метод обработки нажатий кнопок отправить, очистить и цифр
    def on_button_press(self, text_btn, sol_text):

        # Очистка текстового поля с решением
        if text_btn == "Очистка" or (text_btn == "0" and sol_text == "0"):
            return "0"

        # Проверка на корретность номера фонаря
        if text_btn == "Отправить":

            # Если 0 выводим ошибку
            if sol_text == "0":
                return "Ошибка: номер фонаря не можеть быть 0"

            # Если текст то ощибка
            if sol_text == "Отправка: авария" or sol_text == "Ошибка: введите номер фонаря" or \
                    sol_text == "Ошибка: номер фонаря не можеть быть 0" or sol_text == "Номер фонаря отправлен":
                return "Ошибка: введите номер фонаря"

            # Оправка по RS485 строки
            self.write_rs485(sol_text)

            # Вывод в строку
            return "Номер фонаря отправлен"

        # Если цифра то
        if (
                text_btn == "0" or text_btn == "1" or text_btn == "2" or text_btn == "3" or text_btn == "4" or text_btn == "5" or \
                text_btn == "6" or text_btn == "7" or text_btn == "8" or text_btn == "9"):

            # Делаем так чтобы если в тексте стоит 0 не получилось 0000
            if sol_text == "0":
                return text_btn

            # Сброс текста и вывод цифры
            if sol_text == "Ошибка: номер фонаря не можеть быть 0" or sol_text == "Отправка: авария" or \
                    sol_text == "Ошибка: введите номер фонаря" or sol_text == "Номер фонаря отправлен":
                return text_btn
            return sol_text + text_btn

    def on_stop(self):
        if self.serial_port:
            with self.port_thread_lock:
                self.serial_port.close()

    def time_screen(self):
        return date.today()


    def init_com(self):

        self.device_name_list = []

        # For Android
        if platform == 'android':
            usb_device_list = usb.get_usb_device_list()
            self.device_name_list = [device.getDeviceName() for device in usb_device_list]
            device = usb.get_usb_device(self.device_name_list[0])
            if not device:
                raise SerialException(
                   "Device {} not present!".format(self.device_name_list[0])
                )
            if not usb.has_usb_permission(device):
                usb.request_usb_permission(device)
                return
            self.serial_port = serial4a.get_serial_port(self.device_name_list[0], 9600, 8, 'N', 1, timeout=1)

        # For Win and Linux
        else:
            # Setup COM port
            usb_device_list = list_ports.comports()

            if len(usb_device_list) == 0:
                # Screen No Connection
                #self.uiDict['sm'].current = 'screen_view'
                asd=0
            else:
                self.device_name_list = [port.device for port in usb_device_list]
                self.serial_port = Serial(self.device_name_list[0], 9600, 8, 'N', 1, timeout=1)

    def write_rs485(self, data):

        # Read data
        if self.serial_port.is_open and not self.read_thread:
            self.read_thread = threading.Thread(target=self.read_msg_thread)
            self.read_thread.start()

        # Write data to RS485 with convert to bytes
        if self.serial_port and self.serial_port.is_open:
            data_bytes = bytes( (data + '\n'), 'utf8')
            self.serial_port.write(data_bytes)

    def read_msg_thread(self):
        while True:
            try:
                with self.port_thread_lock:
                    if not self.serial_port.is_open:
                        break
                    received_msg = self.serial_port.read(
                        self.serial_port.in_waiting
                    )
                if received_msg:
                    msg = bytes(received_msg).decode('utf8')
                    self.display_received_msg(msg)
            except Exception as ex:
                raise ex

    @mainthread
    def display_received_msg(self, msg):
        self.uiDict['txtInput_read'].text += msg


if __name__ == '__main__':
    MainApp().run()