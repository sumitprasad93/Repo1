import tkinter as tk

class CalculatorApp:
    def __init__(self, master):
        self.master = master
        master.title("Calculator")

        # Display Entry Widget
        self.display_var = tk.StringVar()
        self.display_entry = tk.Entry(master, textvariable=self.display_var, font=('arial', 20, 'bold'), bd=10, insertwidth=2, width=14, borderwidth=4, justify='right', state='readonly')
        self.display_entry.grid(row=0, column=0, columnspan=4, pady=10)
        self.display_var.set("0") # Default display text

        self.first_operand = None
        self.operation = None
        self.waiting_for_second_operand = False

        # Button Creation
        buttons = [
            ('7', 1, 0), ('8', 1, 1), ('9', 1, 2), ('/', 1, 3),
            ('4', 2, 0), ('5', 2, 1), ('6', 2, 2), ('*', 2, 3),
            ('1', 3, 0), ('2', 3, 1), ('3', 3, 2), ('-', 3, 3),
            ('0', 4, 0), ('C', 4, 1), ('=', 4, 2), ('+', 4, 3),
        ]

        for (text, row, col) in buttons:
            button = tk.Button(master, text=text, font=('arial', 18, 'bold'), width=4, height=2, bd=4,
                               command=lambda t=text: self.on_button_click(t))
            button.grid(row=row, column=col, pady=5, padx=5)

    def on_button_click(self, char):
        current_display = self.display_var.get()

        if current_display.startswith("Error"): # If an error is shown, only 'C' should work or new digits
            if char == 'C':
                self.display_var.set("0")
                self.first_operand = None
                self.operation = None
                self.waiting_for_second_operand = False
            elif char.isdigit(): # Allow starting a new number after error, effectively clearing it
                self.display_var.set(char)
                self.first_operand = None
                self.operation = None
                self.waiting_for_second_operand = False
            # Other buttons do nothing if an error is displayed
            return

        if char.isdigit():
            if self.waiting_for_second_operand:
                self.display_var.set(char)
                self.waiting_for_second_operand = False
            elif current_display == "0":
                self.display_var.set(char)
            else:
                self.display_var.set(current_display + char)
        elif char == 'C':
            self.display_var.set("0")
            self.first_operand = None
            self.operation = None
            self.waiting_for_second_operand = False
        elif char in ['+', '-', '*', '/']:
            # Chained operation: e.g. 5 + 3 + (perform 5+3 first)
            if self.first_operand is not None and self.operation is not None and not self.waiting_for_second_operand:
                try:
                    current_val_float = float(current_display)
                    result = self.calculate(self.first_operand, current_val_float, self.operation)
                    self.display_var.set(str(result))
                    self.first_operand = result
                except ValueError:
                    self.display_var.set("Error")
                    self.first_operand = None
                    self.operation = None
                    self.waiting_for_second_operand = False
                    return
                except ZeroDivisionError:
                    self.display_var.set("Error: Division by zero")
                    self.first_operand = None
                    self.operation = None
                    self.waiting_for_second_operand = False
                    return
            
            # Store current value as first_operand for the new operation
            try:
                self.first_operand = float(current_display) # This could be a result of a previous calculation
            except ValueError: # Should not happen if previous logic is sound and errors are caught
                self.display_var.set("Error")
                self.first_operand = None
                self.operation = None
                self.waiting_for_second_operand = False
                return
            self.operation = char
            self.waiting_for_second_operand = True

        elif char == '=':
            if self.first_operand is None or self.operation is None:
                # This can happen if user presses '=' without a full operation, or after an error
                # Or if user presses "5 =" (no operation)
                # We can choose to display an error or do nothing. Let's display Error.
                self.display_var.set("Error")
                self.first_operand = None
                self.operation = None
                self.waiting_for_second_operand = False
                return

            if not self.waiting_for_second_operand: # Standard case: num1 op num2 =
                try:
                    second_operand = float(current_display)
                    result = self.calculate(self.first_operand, second_operand, self.operation)
                    self.display_var.set(str(result))
                    self.first_operand = result 
                    self.waiting_for_second_operand = True 
                except ValueError: # Handles if current_display is not a valid float
                    self.display_var.set("Error")
                    self.first_operand = None
                    self.operation = None
                    self.waiting_for_second_operand = False
                except ZeroDivisionError:
                    self.display_var.set("Error: Division by zero")
                    self.first_operand = None
                    self.operation = None
                    self.waiting_for_second_operand = False
            elif self.waiting_for_second_operand: 
                # Case: num1 op = (uses num1 as num2, e.g. 5 * =)
                # Or num1 op num2 = = (repeats op with previous result and original second_operand - this is more complex)
                # For simplicity, let's assume it repeats the operation with first_operand as both operands if no second one was typed.
                # Example: 5 * =  -> 5 * 5 = 25. Then if = is pressed again, it could be 25 * 5 or 25 * 25.
                # Current logic: 5 * = gives 25 (first_op becomes 25). If = pressed again, it's 25 * 25.
                try:
                    # If waiting for second operand, it implies an operator was just pressed.
                    # If '=' is pressed now, it means we use the first_operand as the second_operand.
                    second_operand = self.first_operand # This was the behavior for "5 * ="
                                        # However, if it was "5 * 3 =", first_operand is 15. waiting_for_second_operand is true.
                                        # Pressing "=" again should ideally use 3 as second_operand.
                                        # This part of logic is tricky. Let's stick to simpler: if waiting_for_second_operand
                                        # and = is pressed, it means an op was just pressed. current_display is first_operand.
                                        # So, it's like num OP = (use num as second operand)
                    
                    # Let's re-evaluate the state for "num op =":
                    # When "num op" is pressed, first_operand is num, operation is op, waiting_for_second_operand is true.
                    # current_display is still "num". If "=" is pressed now.
                    # second_operand should be float(current_display) which is first_operand.
                    
                    second_operand_val = float(current_display) # This should be the value that was on display when op was pressed
                                                              # or the result of the last operation.

                    result = self.calculate(self.first_operand, second_operand_val, self.operation)
                    self.display_var.set(str(result))
                    self.first_operand = result
                    # self.waiting_for_second_operand remains True
                except ValueError: 
                    self.display_var.set("Error")
                    self.first_operand = None
                    self.operation = None
                    self.waiting_for_second_operand = False
                except ZeroDivisionError:
                    self.display_var.set("Error: Division by zero")
                    self.first_operand = None
                    self.operation = None
                    self.waiting_for_second_operand = False


    def calculate(self, n1, n2, op):
        # Ensure n1 is a valid number before calculation, it could be None if previous error
        if n1 is None:
            raise ValueError("First operand is invalid due to previous error.")

        if op == '+':
            return n1 + n2
        elif op == '-':
            return n1 - n2
        elif op == '*':
            return n1 * n2
        elif op == '/':
            if n2 == 0:
                # The specific message is set in on_button_click
                raise ZeroDivisionError("Cannot divide by zero")
            return n1 / n2
        # Removed 'return None' as invalid op should not reach here ideally
        # or could raise an error itself. For now, assume valid ops.

if __name__ == '__main__':
    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()
