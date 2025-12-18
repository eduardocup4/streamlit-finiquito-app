"""
QR code generator and document stamping functionality
"""
import qrcode
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
import json
import base64
from io import BytesIO
import openpyxl
from openpyxl.drawing.image import Image as XLImage

class QRStampGenerator:
    """Generator for QR codes and document stamps"""
    
    def __init__(self, stamp_text: str = "Diseñado por JELB"):
        self.stamp_text = stamp_text
        self.default_qr_size = 150
        self.default_stamp_size = (200, 60)
    
    def generate_qr_code(
        self, 
        data: Dict[str, Any], 
        size: int = None
    ) -> Image.Image:
        """
        Generate QR code from data dictionary
        """
        if size is None:
            size = self.default_qr_size
        
        # Convert data to JSON string
        json_data = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(json_data)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Resize to specified size
        img = img.resize((size, size), Image.Resampling.LANCZOS)
        
        return img
    
    def create_stamp_image(
        self, 
        qr_data: Optional[Dict[str, Any]] = None,
        include_qr: bool = True,
        size: Tuple[int, int] = None
    ) -> Image.Image:
        """
        Create stamp image with QR code and text
        """
        if size is None:
            size = self.default_stamp_size
        
        # Create blank image with white background
        stamp_img = Image.new('RGB', size, color='white')
        draw = ImageDraw.Draw(stamp_img)
        
        # Add border
        border_color = (200, 200, 200)
        draw.rectangle(
            [(0, 0), (size[0]-1, size[1]-1)],
            outline=border_color,
            width=2
        )
        
        # Add QR code if requested
        qr_x_offset = 5
        if include_qr and qr_data:
            qr_size = min(size[1] - 10, 50)
            qr_img = self.generate_qr_code(qr_data, size=qr_size)
            stamp_img.paste(qr_img, (qr_x_offset, (size[1] - qr_size) // 2))
            qr_x_offset += qr_size + 5
        
        # Add text
        try:
            # Try to load a font, fall back to default if not available
            font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 12)
        except:
            font = ImageFont.load_default()
        
        # Draw stamp text
        text_y = size[1] // 2 - 10
        draw.text(
            (qr_x_offset, text_y),
            self.stamp_text,
            fill='black',
            font=font
        )
        
        # Add timestamp
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
        draw.text(
            (qr_x_offset, text_y + 15),
            timestamp,
            fill='gray',
            font=font
        )
        
        return stamp_img
    
    def add_stamp_to_excel(
        self,
        excel_path: str,
        qr_data: Dict[str, Any],
        position: str = "G30",
        sheet_name: Optional[str] = None
    ) -> str:
        """
        Add stamp with QR code to Excel file
        """
        # Load workbook
        wb = openpyxl.load_workbook(excel_path)
        
        # Get worksheet
        if sheet_name:
            ws = wb[sheet_name]
        else:
            ws = wb.active
        
        # Create stamp image
        stamp_img = self.create_stamp_image(qr_data=qr_data)
        
        # Save stamp to temporary BytesIO
        img_buffer = BytesIO()
        stamp_img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # Add image to Excel
        xl_img = XLImage(img_buffer)
        xl_img.anchor = position
        ws.add_image(xl_img)
        
        # Save workbook
        output_path = excel_path.replace('.xlsx', '_stamped.xlsx')
        wb.save(output_path)
        
        return output_path
    
    def generate_verification_payload(
        self,
        calculation_run_id: str,
        document_type: str,
        employee_ci: str,
        timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate payload for QR verification
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        return {
            "id": calculation_run_id,
            "type": document_type,
            "ci": employee_ci,
            "ts": timestamp.isoformat(),
            "v": "1.0"  # Version for future compatibility
        }
    
    def create_removable_stamp_layer(
        self,
        excel_path: str,
        qr_data: Dict[str, Any],
        position: str = "G30"
    ) -> Tuple[str, str]:
        """
        Create a removable stamp layer (returns paths to stamped and clean versions)
        """
        # Create stamped version
        stamped_path = self.add_stamp_to_excel(
            excel_path=excel_path,
            qr_data=qr_data,
            position=position
        )
        
        # Keep original as clean version
        clean_path = excel_path
        
        return stamped_path, clean_path
    
    def encode_stamp_to_base64(self, qr_data: Dict[str, Any]) -> str:
        """
        Encode stamp image to base64 for embedding
        """
        stamp_img = self.create_stamp_image(qr_data=qr_data)
        
        buffer = BytesIO()
        stamp_img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return img_str

class DocumentStampConfig:
    """Configuration for document stamping"""
    
    # Default positions for stamps in different document types
    STAMP_POSITIONS = {
        "f_finiquito": "G35",
        "memo_finalizacion": "F25",
        "rechazo_post": "F20",
        "f_salida": "G30",
        "f_equipos": "G25",
        "contable_preview": "H40"
    }
    
    # Documents that allow internal stamps
    STAMP_ALLOWED = {
        "f_finiquito": False,  # Not allowed per requirements
        "memo_finalizacion": True,
        "rechazo_post": True,
        "f_salida": True,
        "f_equipos": True,
        "contable_preview": True
    }
    
    @classmethod
    def get_stamp_position(cls, document_type: str) -> str:
        """Get default stamp position for document type"""
        return cls.STAMP_POSITIONS.get(document_type, "G30")
    
    @classmethod
    def is_stamp_allowed(cls, document_type: str) -> bool:
        """Check if stamp is allowed for document type"""
        return cls.STAMP_ALLOWED.get(document_type, True)
