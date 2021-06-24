from PyQt5 import QtWidgets
import pandas as pd
import numpy as np
from src.view import ui


def is_leaf(dic, d):
    values = dic.get(d)
    if isinstance(values, dict):
        for k, v in values.items():
            if isinstance(v, dict):
                return False
    return True


def connect_action(action, function):
    if function is not None:
        action.triggered.connect(lambda: function(action))


def menu_from_dict(dic, activation_function=None, menu=None):
    if menu is None:
        menu = QtWidgets.QMenu()
    for k in dic:
        label = dic.get(k).get('label')
        if label is None:
            label = k
        if k.startswith('delimiter'):
            menu.addSeparator()
        elif is_leaf(dic, k):
            act = menu.addAction(label)
            act._type = k
            connect_action(act, activation_function)
        else:
            submenu = menu.addMenu(label)
            menu_from_dict(dic.get(k), activation_function, submenu)
    return menu


def replaceWidget(prev_widget, new_widget):
    layout = prev_widget.parent()
    if isinstance(layout, QtWidgets.QDockWidget):
        layout.setWidget(new_widget)
        prev_widget.deleteLater()
    else:
        if isinstance(layout, QtWidgets.QWidget):
            layout = layout.layout()
        if layout is not None:
            layout.replaceWidget(prev_widget, new_widget)
            prev_widget.deleteLater()
    return new_widget


def getMemoryUsage(object):
    memory = 0
    if isinstance(object, pd.DataFrame):
        memory = object.memory_usage(deep=True).sum()
    for i in ['B', 'KB', 'MB', 'GB']:
        if memory < 1000:
            return memory, i
        memory = int(np.round(memory/1000, 0))


def protector(level="Warning"):
    """
    function used as decorator to avoid the app to crash because of basic errors
    level: {Warning, Critical, Information, Question, NoIcon}
    """
    def decorator(foo):
        def inner(*args, **kwargs):
            try:
                return foo(*args, **kwargs)
            except Exception as e:
                print(e)
                ui.showError(level, e)
                return e
        return inner
    return decorator


def getModifiedFunction(widget):
    if isinstance(widget, (QtWidgets.QCheckBox, QtWidgets.QRadioButton)) or \
       isinstance(widget, QtWidgets.QPushButton) and widget.isCheckable():
        return widget.clicked
    elif isinstance(widget, QtWidgets.QLineEdit):
        return widget.textChanged
    elif isinstance(widget, QtWidgets.QComboBox):
        return widget.editTextChanged
    elif isinstance(widget, QtWidgets.QSpinBox):
        return widget.valueChanged


def getValue(widget):
    if isinstance(widget, (QtWidgets.QCheckBox, QtWidgets.QRadioButton)) or \
       isinstance(widget, QtWidgets.QPushButton) and widget.isCheckable():
        return widget.isChecked()
    elif isinstance(widget, QtWidgets.QLineEdit):
        return widget.text()
    elif isinstance(widget, QtWidgets.QComboBox):
        return widget.currentText()
    elif isinstance(widget, QtWidgets.QSpinBox):
        return widget.value()
    elif isinstance(widget, ui.QGridButtonGroup):
        return widget.checkedButtonsText()
    elif isinstance(widget, ui.QTypeForm):
        values = {}
        for name, row in widget.rows.items():
            values[name] = [getValue(row.types), getValue(row.format),
                            getValue(row.unit), getValue(row.force)]
        return values


def setValue(widget, value):
    if isinstance(widget, (QtWidgets.QCheckBox, QtWidgets.QRadioButton)) or \
       isinstance(widget, QtWidgets.QPushButton) and widget.isCheckable():
        widget.setChecked(value)
        widget.clicked.emit()
    elif isinstance(widget, QtWidgets.QLineEdit):
        widget.setText(value)
        widget.editingFinished.emit()
    elif isinstance(widget, QtWidgets.QComboBox):
        widget.setCurrentText(value)
    elif isinstance(widget, QtWidgets.QSpinBox):
        widget.setValue(value)
    elif isinstance(widget, ui.QGridButtonGroup):
        for button in widget.group.buttons():
            setValue(button, button.text() in value)
    elif isinstance(widget, ui.QTypeForm):
        for name, row in widget.rows.items():
            if name in value:
                setValue(row.types,  value[name][0])
                setValue(row.format, value[name][1])
                setValue(row.unit,   value[name][2])
                setValue(row.force,  value[name][3])