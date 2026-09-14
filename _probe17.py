# -*- coding: utf-8 -*-
import urllib.parse

cap = "O64VkH6LO2%2FjCp%2FGmOrueea5CHg%2FNP8yhHiKWNfHCxLTyZebV7-3CpSLnoFx4xQYU8kVpF37GDz%2FYDVcZW7spHnkompvSg7blU5InX6LgqiXPl40LqDxezgzqXsCWRGqlA5AiAJIhUJ71nd-iqQL%2FpVCyKOFQQWh%2F1O6k2zSY9ahZ0yAg3n-PQbpTXTqSj%3D%3D"
dec = urllib.parse.unquote(cap)
print("captured raw len:", len(cap), "decoded len:", len(dec))
print("decoded:", dec)

mine = "OyUnktW7dN5VKpKSYKn-t9o5W0IMrNWypM4ORRqr9xFByZ0T3X-eAkuMroFSsDKDtWkCpq17nE0AYxVcplX03CnpFmkfu8kRe0onnXmoZHL0GBvhrHLiKEGELiTb0A4YmQAtE/fRXs0KIDOW9N9TAQaHw/W68ei/M1PGdemcq9-L"
print("mine len:", len(mine))
