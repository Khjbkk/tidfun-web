"""Generate PromptPay QR PNGs (one per price) into public/qr/<amount>.png.

Usage: python3 scripts/make_qr.py 0812345678            (phone)
       python3 scripts/make_qr.py 1234567890123         (national ID / tax ID)
Requires: pip install qrcode pillow
"""
import os
import sys

import qrcode

AMOUNTS = [99, 119, 129, 148, 168, 178, 490]


def tlv(tag, value):
    return f"{tag}{len(value):02d}{value}"


def crc16(data):
    crc = 0xFFFF
    for b in data.encode("ascii"):
        crc ^= b << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) if crc & 0x8000 else (crc << 1)
            crc &= 0xFFFF
    return f"{crc:04X}"


def promptpay_payload(target, amount):
    digits = "".join(c for c in target if c.isdigit())
    # PromptPay targets are a mobile number (10 digits starting with 0) or a 13-digit
    # national/tax ID. A bank account number is NOT a PromptPay ID: encoding it would
    # silently send customers' money to a different phone-number account.
    if not ((len(digits) == 10 and digits.startswith("0")) or len(digits) == 13):
        sys.exit(f"'{target}' is not a PromptPay ID (need 10-digit mobile starting with 0, or 13-digit tax/national ID). No QR generated.")
    if len(digits) == 13:
        acct = tlv("02", digits)  # national ID / tax ID
    else:
        acct = tlv("01", ("0066" + digits[1:]).rjust(13, "0"))  # mobile number
    merchant = tlv("00", "A000000677010111") + acct
    body = (
        tlv("00", "01")
        + tlv("01", "12")  # dynamic QR (has amount)
        + tlv("29", merchant)
        + tlv("53", "764")  # THB
        + tlv("54", f"{amount:.2f}")
        + tlv("58", "TH")
        + "6304"
    )
    return body + crc16(body)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    out = os.path.join(os.path.dirname(__file__), "..", "public", "qr")
    os.makedirs(out, exist_ok=True)
    for amount in AMOUNTS:
        img = qrcode.make(promptpay_payload(sys.argv[1], amount), box_size=12, border=3)
        img.save(os.path.join(out, f"{amount}.png"))
        print(f"public/qr/{amount}.png  ({amount} THB)")


if __name__ == "__main__":
    main()
