import unittest
from src.lbx_utils.layout_engine import FlexLayoutEngine
from src.lbx_utils.models import LabelConfig
from src.lbx_utils.models.text import TextObject

class TestOffsetWithLayout(unittest.TestCase):
    def setUp(self):
        self.engine = FlexLayoutEngine()

    def test_x_offset_with_row_layout(self):
        """Test that x values act as offsets in row layout."""
        # Create a config with root-level row layout
        config = LabelConfig(
            size="24mm",
            width="100mm",
            direction="row",  # Horizontal layout
            align="center",
            justify="start",
            gap=10,
            has_root_layout=True,
            apply_root_layout=True,
            objects=[]
        )

        # Add objects with x offsets
        text1 = TextObject(
            text="First Item",
            x="0pt",  # No offset
            y="0pt",
            width="50pt",
            height="20pt"
        )

        text2 = TextObject(
            text="Second Item",
            x="10pt",  # 10pt offset to the right
            y="0pt",
            width="50pt",
            height="20pt"
        )

        text3 = TextObject(
            text="Third Item",
            x="20pt",  # 20pt offset to the right
            y="0pt",
            width="50pt",
            height="20pt"
        )

        config.objects = [text1, text2, text3]

        # Apply layout
        self.engine.apply_root_layout(config)

        # Get x values
        x1 = float(text1.x.replace('pt', ''))
        x2 = float(text2.x.replace('pt', ''))
        x3 = float(text3.x.replace('pt', ''))

        # Calculate expected positions
        # text1 should be at padding.left + 0pt offset
        # text2 should be at text1's right edge + gap + 10pt offset
        # text3 should be at text2's right edge + gap + 20pt offset
        expected_x1 = 0  # No offset
        expected_x2_without_offset = expected_x1 + 50 + 10  # text1 width + gap
        expected_x3_without_offset = expected_x2_without_offset + 10 + 50 + 10  # text2 offset + text2 width + gap

        # Verify that offsets are applied correctly
        self.assertAlmostEqual(x2 - expected_x2_without_offset, 10, delta=1)  # 10pt offset
        self.assertAlmostEqual(x3 - expected_x3_without_offset, 20, delta=1)  # 20pt offset

    def test_y_offset_with_column_layout(self):
        """Test that y values act as offsets in column layout."""
        # Create a config with root-level column layout
        config = LabelConfig(
            size="24mm",
            width="100mm",
            direction="column",  # Vertical layout
            align="center",
            justify="start",
            gap=10,
            has_root_layout=True,
            apply_root_layout=True,
            objects=[]
        )

        # Add objects with y offsets
        text1 = TextObject(
            text="First Item",
            x="0pt",
            y="0pt",  # No offset
            width="50pt",
            height="20pt"
        )

        text2 = TextObject(
            text="Second Item",
            x="0pt",
            y="15pt",  # 15pt offset down
            width="50pt",
            height="20pt"
        )

        text3 = TextObject(
            text="Third Item",
            x="0pt",
            y="30pt",  # 30pt offset down
            width="50pt",
            height="20pt"
        )

        config.objects = [text1, text2, text3]

        # Apply layout
        self.engine.apply_root_layout(config)

        # Get y values
        y1 = float(text1.y.replace('pt', ''))
        y2 = float(text2.y.replace('pt', ''))
        y3 = float(text3.y.replace('pt', ''))

        # Calculate expected positions
        # text1 should be at padding.top + 0pt offset
        # text2 should be at text1's bottom edge + gap + 15pt offset
        # text3 should be at text2's bottom edge + gap + 30pt offset
        expected_y1 = 0  # No offset
        expected_y2_without_offset = expected_y1 + 20 + 10  # text1 height + gap
        expected_y3_without_offset = expected_y2_without_offset + 15 + 20 + 10  # text2 offset + text2 height + gap

        # Verify that offsets are applied correctly
        self.assertAlmostEqual(y2 - expected_y2_without_offset, 15, delta=1)  # 15pt offset
        self.assertAlmostEqual(y3 - expected_y3_without_offset, 30, delta=1)  # 30pt offset

    def test_offset_propagation_in_row_layout(self):
        """Test that an offset on one item affects the position of subsequent items in row layout."""
        config = LabelConfig(
            size="24mm",
            width="100mm",
            direction="row",
            align="start",
            justify="start",
            gap=10,
            has_root_layout=True,
            apply_root_layout=True,
            objects=[]
        )

        # First run - without offset on first item
        text1 = TextObject(
            text="First Item",
            x="0pt",
            y="0pt",
            width="50pt",
            height="20pt"
        )

        text2 = TextObject(
            text="Second Item",
            x="0pt",
            y="0pt",
            width="50pt",
            height="20pt"
        )

        text3 = TextObject(
            text="Third Item",
            x="0pt",
            y="0pt",
            width="50pt",
            height="20pt"
        )

        config.objects = [text1, text2, text3]
        self.engine.apply_root_layout(config)

        # Get positions without offset
        x2_without_offset = float(text2.x.replace('pt', ''))
        x3_without_offset = float(text3.x.replace('pt', ''))

        # Second run - with offset on first item
        text1_offset = TextObject(
            text="First Item",
            x="25pt",  # 25pt offset
            y="0pt",
            width="50pt",
            height="20pt"
        )

        text2_offset = TextObject(
            text="Second Item",
            x="0pt",
            y="0pt",
            width="50pt",
            height="20pt"
        )

        text3_offset = TextObject(
            text="Third Item",
            x="0pt",
            y="0pt",
            width="50pt",
            height="20pt"
        )

        config.objects = [text1_offset, text2_offset, text3_offset]
        self.engine.apply_root_layout(config)

        # Get positions with offset
        x2_with_offset = float(text2_offset.x.replace('pt', ''))
        x3_with_offset = float(text3_offset.x.replace('pt', ''))

        # The positions of subsequent items should be shifted by 25pt
        self.assertAlmostEqual(x2_with_offset - x2_without_offset, 25, delta=1)
        self.assertAlmostEqual(x3_with_offset - x3_without_offset, 25, delta=1)

    def test_offset_propagation_in_column_layout(self):
        """Test that an offset on one item affects the position of subsequent items in column layout."""
        config = LabelConfig(
            size="24mm",
            width="100mm",
            direction="column",
            align="start",
            justify="start",
            gap=10,
            has_root_layout=True,
            apply_root_layout=True,
            objects=[]
        )

        # First run - without offset on first item
        text1 = TextObject(
            text="First Item",
            x="0pt",
            y="0pt",
            width="50pt",
            height="20pt"
        )

        text2 = TextObject(
            text="Second Item",
            x="0pt",
            y="0pt",
            width="50pt",
            height="20pt"
        )

        text3 = TextObject(
            text="Third Item",
            x="0pt",
            y="0pt",
            width="50pt",
            height="20pt"
        )

        config.objects = [text1, text2, text3]
        self.engine.apply_root_layout(config)

        # Get positions without offset
        y2_without_offset = float(text2.y.replace('pt', ''))
        y3_without_offset = float(text3.y.replace('pt', ''))

        # Second run - with offset on first item
        text1_offset = TextObject(
            text="First Item",
            x="0pt",
            y="25pt",  # 25pt offset
            width="50pt",
            height="20pt"
        )

        text2_offset = TextObject(
            text="Second Item",
            x="0pt",
            y="0pt",
            width="50pt",
            height="20pt"
        )

        text3_offset = TextObject(
            text="Third Item",
            x="0pt",
            y="0pt",
            width="50pt",
            height="20pt"
        )

        config.objects = [text1_offset, text2_offset, text3_offset]
        self.engine.apply_root_layout(config)

        # Get positions with offset
        y2_with_offset = float(text2_offset.y.replace('pt', ''))
        y3_with_offset = float(text3_offset.y.replace('pt', ''))

        # The positions of subsequent items should be shifted by 25pt
        self.assertAlmostEqual(y2_with_offset - y2_without_offset, 25, delta=1)
        self.assertAlmostEqual(y3_with_offset - y3_without_offset, 25, delta=1)

if __name__ == '__main__':
    unittest.main()