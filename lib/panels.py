import sublime

TIMEOUT = 50
class MultiSelect(object):
    """Opens a quick panel for multiple selection"""

    def __init__(self, items, on_complete, on_cancel=None, show_select_all=False):
        """Constructs the MultiSelect"""
        self.values = []
        self.items = []
        self.on_complete = on_complete
        self.on_cancel = on_cancel
        self.values.append('done')
        self.items.append('Done')
        if show_select_all:
            self.values.append('select')
            self.items.append('Select All')
            self.values.append('deselect')
            self.items.append('Unselect All')
        for item in items:
            if isinstance(item, str):
                self.values.append({
                    'label': item,
                    'value': item,
                    'selected': False
                })
                self.items.append(self.add_check(item, False))
            else:
                panel_item = {
                    'label': item['label'] or item['value'],
                    'value': item['value'] or item['label'],
                    'selected': bool(item['selected']) or False
                }
                self.values.append(panel_item)
                self.items.append(self.add_check(panel_item['label'], panel_item['selected']))
        self.open()

    def add_check(self, label, selected=False):
        """Adds a checkmark to the label"""
        if isinstance(label, list):
            label = list(label)
            if selected:
                label[0] = '[X] ' + label[0]
            else:
                label[0] = '[ ] ' + label[0]
        else:
            if selected:
                label = '[X] ' + label
            else:
                label = '[ ] ' + label
        return label

    def done(self):
        """Sends the selected values to the complete callback"""
        vals = []
        for val in self.values:
            if isinstance(val, str):
                continue
            if val['selected']:
                vals.append(val['value'])
        self.on_complete(vals)

    def cancel(self):
        """Cancels the MultiSelect panel"""
        if self.on_cancel is not None:
            self.on_cancel()

    def all(self, select):
        """Set the selected state of all items"""
        for index, item in enumerate(self.values):
            if isinstance(item, str):
                continue
            item['selected'] = select
            self.items[index] = self.add_check(item['label'], select)

    def select(self, index):
        """Selects an item from the MultiSelect panel"""
        if index == -1:
            self.cancel()
            return
        val = self.values[index]
        if isinstance(val, str):
            if val == 'done':
                self.done()
                return
            elif val == 'select':
                self.all(True)
            elif val == 'deselect':
                self.all(False)
        else:
            val['selected'] = not val['selected']
            label = self.add_check(val['label'], val['selected'])
            self.items[index] = label
        self.reopen()

    def reopen(self):
        """Opens the MultiSelect again"""
        sublime.set_timeout(self.open, TIMEOUT)

    def open(self):
        """Opens the MultiSelect panel"""
        sublime.active_window().show_quick_panel(self.items, self.select, sublime.MONOSPACE_FONT)