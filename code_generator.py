# code_generator.py
# FeedbackBot
# Created by romanesin on 16.07.2021
import qrcode


def generate_qr_code(data: str, img_name: str):
    qr = qrcode.QRCode(version=1,
                       error_correction=qrcode.constants.ERROR_CORRECT_L,
                       box_size=10,
                       border=1)

    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(img_name)

    print("Creating img:", img_name)
