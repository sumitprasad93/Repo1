import unittest
import tkinter as tk
# Assuming calculator_gui.py contains the CalculatorApp class
from calculator_gui import CalculatorApp

class TestCalculatorLogic(unittest.TestCase):
    def setUp(self):
        # Create a dummy Tk root window for the CalculatorApp instance
        # This window will not be shown or enter mainloop during tests
        self.root = tk.Tk()
        self.app = CalculatorApp(self.root)
        # Ensure a clean state for each test by simulating 'C' (Clear)
        self.app.on_button_click('C')

    def tearDown(self):
        # Destroy the dummy root window after each test
        self.root.destroy()

    # Tests for the calculate() method
    def test_calculate_addition(self):
        self.assertEqual(self.app.calculate(5, 3, '+'), 8)
        self.assertEqual(self.app.calculate(-5, 3, '+'), -2)
        self.assertEqual(self.app.calculate(0, 0, '+'), 0)
        self.assertEqual(self.app.calculate(1.5, 2.5, '+'), 4.0)

    def test_calculate_subtraction(self):
        self.assertEqual(self.app.calculate(5, 3, '-'), 2)
        self.assertEqual(self.app.calculate(-5, 3, '-'), -8)
        self.assertEqual(self.app.calculate(3, 5, '-'), -2)
        self.assertEqual(self.app.calculate(2.5, 1.5, '-'), 1.0)

    def test_calculate_multiplication(self):
        self.assertEqual(self.app.calculate(5, 3, '*'), 15)
        self.assertEqual(self.app.calculate(-5, 3, '*'), -15)
        self.assertEqual(self.app.calculate(5, 0, '*'), 0)
        self.assertEqual(self.app.calculate(1.5, 2, '*'), 3.0)

    def test_calculate_division(self):
        self.assertEqual(self.app.calculate(6, 3, '/'), 2)
        self.assertEqual(self.app.calculate(-6, 3, '/'), -2)
        self.assertEqual(self.app.calculate(0, 5, '/'), 0)
        self.assertEqual(self.app.calculate(5, 2, '/'), 2.5)

    def test_calculate_division_by_zero(self):
        with self.assertRaisesRegex(ZeroDivisionError, "Cannot divide by zero"):
            self.app.calculate(5, 0, '/')

    def test_calculate_first_operand_none(self):
        # As per current implementation, calculate() checks if n1 is None
        with self.assertRaisesRegex(ValueError, "First operand is invalid due to previous error."):
            self.app.calculate(None, 5, '+')

    # Tests for on_button_click() method - GUI interaction simulation
    def _press_buttons(self, sequence):
        """Helper function to simulate a sequence of button presses."""
        for char in sequence:
            self.app.on_button_click(char)

    # --- Number Input Tests ---
    def test_number_input_simple(self):
        self._press_buttons("123")
        self.assertEqual(self.app.display_var.get(), "123")

    def test_number_input_leading_zero_replace(self):
        self._press_buttons("0")
        self.assertEqual(self.app.display_var.get(), "0")
        self._press_buttons("5") # Should replace "0"
        self.assertEqual(self.app.display_var.get(), "5")

    def test_number_input_multiple_zeros_then_digit(self):
        self._press_buttons("000") # Should remain "0"
        self.assertEqual(self.app.display_var.get(), "0")
        self._press_buttons("5")
        self.assertEqual(self.app.display_var.get(), "5")


    def test_number_input_after_operator(self):
        self._press_buttons("5+")
        self.assertTrue(self.app.waiting_for_second_operand) # After operator, waiting is true
        self._press_buttons("3")
        self.assertEqual(self.app.display_var.get(), "3") # Display shows second operand
        self.assertFalse(self.app.waiting_for_second_operand) # After digit input, waiting is false

    def test_number_input_after_equals(self):
        self._press_buttons("5+3=") # Display is "8.0"
        self.assertEqual(self.app.display_var.get(), "8.0")
        self._press_buttons("9") # Start new number
        self.assertEqual(self.app.display_var.get(), "9")
        self.assertFalse(self.app.waiting_for_second_operand)

    # --- Clear Button ('C') Test ---
    def test_clear_button(self):
        self._press_buttons("123+45=")
        self.assertNotEqual(self.app.display_var.get(), "0")
        self.assertIsNotNone(self.app.first_operand)
        # self.assertIsNotNone(self.app.operation) # Operation is cleared after equals in current logic
        
        self._press_buttons("C")
        self.assertEqual(self.app.display_var.get(), "0")
        self.assertIsNone(self.app.first_operand)
        self.assertIsNone(self.app.operation)
        self.assertFalse(self.app.waiting_for_second_operand)

    def test_clear_button_mid_input(self):
        self._press_buttons("123+")
        self._press_buttons("C")
        self.assertEqual(self.app.display_var.get(), "0")
        self.assertIsNone(self.app.first_operand) # first_operand is set only when an op is followed by num or another op or =
        self.assertIsNone(self.app.operation)
        self.assertFalse(self.app.waiting_for_second_operand)
        # Test if we can start a new calculation
        self._press_buttons("7*2=")
        self.assertEqual(self.app.display_var.get(), "14.0")


    # --- Operations Tests ---
    def test_operation_storage(self):
        self._press_buttons("789+")
        self.assertEqual(self.app.first_operand, 789.0)
        self.assertEqual(self.app.operation, "+")
        self.assertTrue(self.app.waiting_for_second_operand)
        self.assertEqual(self.app.display_var.get(), "789") # Display still shows first operand until second is typed

        self._press_buttons("12") # Start typing second operand
        self.assertFalse(self.app.waiting_for_second_operand) # Now false
        self.assertEqual(self.app.display_var.get(), "12")


    # --- Equals Button Tests ---
    def test_equals_simple_addition(self):
        self._press_buttons("5+3=")
        self.assertEqual(self.app.display_var.get(), "8.0")
        self.assertEqual(self.app.first_operand, 8.0) # Result stored in first_operand
        self.assertTrue(self.app.waiting_for_second_operand) # Ready for new number or chained op

    def test_equals_simple_subtraction(self):
        self._press_buttons("10-4=")
        self.assertEqual(self.app.display_var.get(), "6.0")

    def test_equals_simple_multiplication(self):
        self._press_buttons("6*7=")
        self.assertEqual(self.app.display_var.get(), "42.0")

    def test_equals_simple_division(self):
        self._press_buttons("10/4=") # Result is 2.5
        self.assertEqual(self.app.display_var.get(), "2.5")

    def test_chained_operations(self):
        self._press_buttons("5+3+2=") # (5+3)=8, then 8+2=10
        self.assertEqual(self.app.display_var.get(), "10.0")
        self.assertEqual(self.app.first_operand, 10.0)

    def test_chained_operations_mixed(self):
        self._press_buttons("10-2*3=") # (10-2)=8, then 8*3=24
        self.assertEqual(self.app.display_var.get(), "24.0")

    def test_chained_operations_then_new_op(self):
        self._press_buttons("10-2*") # (10-2)=8. first_operand=8, operation='*'
        self.assertEqual(self.app.display_var.get(), "8.0") # Shows result of 10-2
        self.assertEqual(self.app.first_operand, 8.0)
        self.assertEqual(self.app.operation, "*")
        self.assertTrue(self.app.waiting_for_second_operand)
        self._press_buttons("3=") # 8*3=24
        self.assertEqual(self.app.display_var.get(), "24.0")

    def test_repeated_equals_multiplication(self):
        # "5 * = " should be 5*5=25
        self._press_buttons("5*=")
        self.assertEqual(self.app.display_var.get(), "25.0")
        self.assertEqual(self.app.first_operand, 25.0)
        # Pressing "=" again: current logic 25*25 = 625 (uses display as second operand)
        self._press_buttons("=")
        self.assertEqual(self.app.display_var.get(), "625.0")
        self.assertEqual(self.app.first_operand, 625.0)

    def test_repeated_equals_after_full_op(self):
        # "5 * 2 = =" should be 5*2=10, then 10*10 = 100 (based on current logic where first_op is result, and display is result)
        self._press_buttons("5*2=")
        self.assertEqual(self.app.display_var.get(), "10.0") # 5*2=10
        self.assertEqual(self.app.first_operand, 10.0)
        self._press_buttons("=") # current_display is 10.0, first_operand is 10.0. So 10.0 * 10.0
        self.assertEqual(self.app.display_var.get(), "100.0") # 10 * 10 = 100

    # --- Error Handling Simulation Tests ---
    def test_error_division_by_zero(self):
        self._press_buttons("1/0=")
        self.assertEqual(self.app.display_var.get(), "Error: Division by zero")
        self.assertIsNone(self.app.first_operand)
        self.assertIsNone(self.app.operation)
        self.assertFalse(self.app.waiting_for_second_operand)

    def test_error_operator_without_first_number(self):
        self._press_buttons("+") # No first number
        # Current logic: sets first_operand to 0.0 if display is "0", then op to "+"
        # This is not necessarily an error state until "=" is pressed without a second number
        # Or if we try 0/0.
        # Let's test pressing "=" after just an operator
        self.app.on_button_click('C') # Clear first
        self._press_buttons("+=")
        self.assertEqual(self.app.display_var.get(), "Error") # first_operand=0, op="+", no second_operand

    def test_error_invalid_operation_sequence_equals_only(self):
        self._press_buttons("=")
        self.assertEqual(self.app.display_var.get(), "Error")

    def test_error_reset_with_c_after_error(self):
        self._press_buttons("1/0=") # Error state
        self.assertEqual(self.app.display_var.get(), "Error: Division by zero")
        self._press_buttons("C")
        self.assertEqual(self.app.display_var.get(), "0")
        self.assertIsNone(self.app.first_operand)
        self.assertIsNone(self.app.operation)
        self.assertFalse(self.app.waiting_for_second_operand)
        # Check if calculator works after reset
        self._press_buttons("1+1=")
        self.assertEqual(self.app.display_var.get(), "2.0")

    def test_error_new_digit_clears_error(self):
        self._press_buttons("1/0=") # Error state
        self.assertEqual(self.app.display_var.get(), "Error: Division by zero")
        self._press_buttons("5") # New digit
        self.assertEqual(self.app.display_var.get(), "5") # Error cleared, new number started
        self.assertIsNone(self.app.first_operand)
        self.assertIsNone(self.app.operation)
        self.assertFalse(self.app.waiting_for_second_operand)
        # Check if calculator works
        self._press_buttons("+2=")
        self.assertEqual(self.app.display_var.get(), "7.0") # 5+2=7

    def test_operator_after_error_is_ignored(self):
        self._press_buttons("1/0=") # Error state
        self.assertEqual(self.app.display_var.get(), "Error: Division by zero")
        self._press_buttons("+") # Operator after error
        self.assertEqual(self.app.display_var.get(), "Error: Division by zero") # Should remain error
        self.assertIsNone(self.app.first_operand) # State should not have changed
        self.assertIsNone(self.app.operation)

    def test_equals_after_error_is_ignored(self):
        self._press_buttons("1/0=") # Error state
        self.assertEqual(self.app.display_var.get(), "Error: Division by zero")
        self._press_buttons("=") # Equals after error
        self.assertEqual(self.app.display_var.get(), "Error: Division by zero") # Should remain error
        self.assertIsNone(self.app.first_operand)
        self.assertIsNone(self.app.operation)

if __name__ == '__main__':
    unittest.main()
