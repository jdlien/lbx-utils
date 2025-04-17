import unittest
from src.lbx_utils.layout_engine import FlexLayoutEngine
from src.lbx_utils.models import GroupObject
from src.lbx_utils.models.text import TextObject, FontInfo

class TestFlexLayoutEngine(unittest.TestCase):
    def setUp(self):
        self.engine = FlexLayoutEngine()

    def test_row_layout_with_center_align(self):
        """Test that items are properly centered vertically in a row layout."""
        # Create a group with row direction and center alignment
        group = GroupObject(
            x="0pt",
            y="0pt",
            width="200pt",
            height="100pt",
            direction="row",
            align="center",
            gap=10,
            objects=[]
        )

        # Add objects of different heights
        text1 = TextObject(
            text="Short",
            x="0pt",
            y="0pt",
            width="50pt",
            height="20pt"
        )

        text2 = TextObject(
            text="Tall Item",
            x="0pt",
            y="0pt",
            width="50pt",
            height="60pt"  # This is the tallest item
        )

        text3 = TextObject(
            text="Medium",
            x="0pt",
            y="0pt",
            width="50pt",
            height="40pt"
        )

        group.objects = [text1, text2, text3]

        # Apply layout
        self.engine.apply_layout(group)

        # Get y-coordinate values and convert to float
        y1 = float(text1.y.replace('pt', ''))
        y2 = float(text2.y.replace('pt', ''))
        y3 = float(text3.y.replace('pt', ''))

        # Check that shorter items are centered relative to the tallest item
        # For text1 (height 20), in a container of height 100 with tallest item 60:
        # Expected y position should be (100 - 20) / 2 = 40
        self.assertAlmostEqual(y1, 40, delta=1)

        # For text2 (height 60), which is the tallest:
        # Expected y position should be (100 - 60) / 2 = 20
        self.assertAlmostEqual(y2, 20, delta=1)

        # For text3 (height 40):
        # Expected y position should be (100 - 40) / 2 = 30
        self.assertAlmostEqual(y3, 30, delta=1)

    def test_column_layout_with_center_align(self):
        """Test that items are properly centered horizontally in a column layout."""
        # Create a group with column direction and center alignment
        group = GroupObject(
            x="0pt",
            y="0pt",
            width="200pt",
            height="200pt",
            direction="column",
            align="center",
            gap=10,
            objects=[]
        )

        # Add objects of different widths
        text1 = TextObject(
            text="Narrow",
            x="0pt",
            y="0pt",
            width="50pt",
            height="20pt"
        )

        text2 = TextObject(
            text="Wide Item That Needs More Space",
            x="0pt",
            y="0pt",
            width="150pt",  # This is the widest item
            height="20pt"
        )

        text3 = TextObject(
            text="Medium Width",
            x="0pt",
            y="0pt",
            width="100pt",
            height="20pt"
        )

        group.objects = [text1, text2, text3]

        # Apply layout
        self.engine.apply_layout(group)

        # Get x-coordinate values and convert to float
        x1 = float(text1.x.replace('pt', ''))
        x2 = float(text2.x.replace('pt', ''))
        x3 = float(text3.x.replace('pt', ''))

        # Check that narrower items are centered
        # For text1 (width 50), in a container of width 200:
        # Expected x position should be (200 - 50) / 2 = 75
        self.assertAlmostEqual(x1, 75, delta=1)

        # For text2 (width 150), which is the widest:
        # Expected x position should be (200 - 150) / 2 = 25
        self.assertAlmostEqual(x2, 25, delta=1)

        # For text3 (width 100):
        # Expected x position should be (200 - 100) / 2 = 50
        self.assertAlmostEqual(x3, 50, delta=1)

    def test_nested_layouts(self):
        """Test that nested groups with different alignments work correctly."""
        # Create outer group with row direction
        outer_group = GroupObject(
            x="0pt",
            y="0pt",
            width="300pt",
            height="200pt",
            direction="row",
            align="center",
            gap=20,
            objects=[]
        )

        # Create inner group with column direction
        inner_group = GroupObject(
            x="0pt",
            y="0pt",
            width="100pt",
            height="150pt",
            direction="column",
            align="center",
            gap=10,
            objects=[]
        )

        # Add items to inner group
        inner_text1 = TextObject(
            text="Inner Top",
            x="0pt",
            y="0pt",
            width="80pt",
            height="30pt"
        )

        inner_text2 = TextObject(
            text="Inner Bottom",
            x="0pt",
            y="0pt",
            width="60pt",
            height="30pt"
        )

        inner_group.objects = [inner_text1, inner_text2]

        # Add another item to outer group
        outer_text = TextObject(
            text="Outer Item",
            x="0pt",
            y="0pt",
            width="100pt",
            height="80pt"
        )

        # Assemble the groups
        outer_group.objects = [inner_group, outer_text]

        # Apply layout
        self.engine.apply_layout(outer_group)

        # The inner group should be centered vertically in the outer group
        inner_group_y = float(inner_group.y.replace('pt', ''))

        # Expected y position of inner group (height 150) in container of height 200:
        # (200 - 150) / 2 = 25
        self.assertAlmostEqual(inner_group_y, 25, delta=1)

        # Inner items should be centered horizontally in the inner group
        inner_text1_x = float(inner_text1.x.replace('pt', ''))
        inner_text2_x = float(inner_text2.x.replace('pt', ''))

        # Expected x position of inner_text1 (width 80) in inner group of width 100:
        # inner_group_x + (100 - 80) / 2 = inner_group_x + 10
        inner_group_x = float(inner_group.x.replace('pt', ''))
        self.assertAlmostEqual(inner_text1_x, inner_group_x + 10, delta=1)

        # Expected x position of inner_text2 (width 60) in inner group of width 100:
        # inner_group_x + (100 - 60) / 2 = inner_group_x + 20
        self.assertAlmostEqual(inner_text2_x, inner_group_x + 20, delta=1)

if __name__ == '__main__':
    unittest.main()