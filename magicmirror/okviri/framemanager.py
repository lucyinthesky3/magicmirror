class FrameManager:
    okviri = {}

    @staticmethod
    def dodaj_okvir(naziv, okvir):
        FrameManager.okviri.update({naziv: okvir})

    @staticmethod
    def prikazi_okvir(naziv_okvira):
        okvir = FrameManager.okviri.get(naziv_okvira)
        okvir.tkraise()