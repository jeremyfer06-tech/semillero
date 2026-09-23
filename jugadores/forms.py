from django import forms

from .models import Equipo, EstadisticaJuego, Jugador, Partido, Posicion, Video


class EquipoForm(forms.ModelForm):
    class Meta:
        model = Equipo
        fields = ['campeonato', 'escuadra']
        widgets = {
            'escuadra': forms.TextInput(attrs={'placeholder': 'Ej: A, D, D1 (déjalo vacío si no aplica)'}),
        }
        labels = {
            'campeonato': 'Categoría / temporada',
        }

    def __init__(self, *args, club=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.club = club

    def save(self, commit=True):
        equipo = super().save(commit=False)
        equipo.club = self.club
        if commit:
            equipo.save()
        return equipo


class JugadorForm(forms.ModelForm):
    class Meta:
        model = Jugador
        fields = ['nombre', 'fecha_nacimiento', 'equipo', 'posicion_campo', 'foto']
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, club=None, **kwargs):
        super().__init__(*args, **kwargs)
        if club is not None:
            self.fields['equipo'].queryset = Equipo.objects.filter(club=club).select_related(
                'campeonato', 'campeonato__categoria',
            )


class VideoForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ['tipo_toma', 'archivo', 'visibilidad']

    def __init__(self, *args, juego=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.juego = juego

    def save(self, commit=True):
        video = super().save(commit=False)
        video.jugador = self.juego.jugador
        video.juego = self.juego
        video.fecha = self.juego.fecha
        if commit:
            video.save()
        return video


class PartidoForm(forms.ModelForm):
    class Meta:
        model = Partido
        fields = ['equipo_local', 'equipo_visitante', 'fecha', 'hora', 'estadio']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'hora': forms.TimeInput(attrs={'type': 'time'}),
        }
        labels = {'equipo_local': 'Equipo local', 'equipo_visitante': 'Equipo visitante'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        etiqueta = lambda e: f"{e} — {e.campeonato.categoria.nombre} ({e.campeonato.temporada})"
        qs = Equipo.objects.select_related('campeonato', 'campeonato__categoria', 'club').order_by(
            'campeonato__categoria__orden', 'club__nombre', 'escuadra',
        )
        for campo in ('equipo_local', 'equipo_visitante'):
            self.fields[campo].queryset = qs
            self.fields[campo].label_from_instance = etiqueta

    def clean(self):
        cleaned = super().clean()
        local, visitante = cleaned.get('equipo_local'), cleaned.get('equipo_visitante')
        if local and visitante:
            if local == visitante:
                raise forms.ValidationError('El equipo local y el visitante no pueden ser el mismo.')
            if local.campeonato_id != visitante.campeonato_id:
                raise forms.ValidationError(
                    'Los dos equipos deben pertenecer a la misma categoría y temporada.'
                )
        return cleaned

    def save(self, commit=True):
        partido = super().save(commit=False)
        partido.campeonato = partido.equipo_local.campeonato
        if commit:
            partido.save()
        return partido


class EstadisticaJuegoForm(forms.ModelForm):
    class Meta:
        model = EstadisticaJuego
        fields = [
            'posicion_jugada',
            'turnos', 'hits', 'dobles', 'triples', 'jonrones',
            'carreras_anotadas', 'impulsadas', 'bases_robadas', 'ponches', 'base_por_bolas',
            'putouts', 'asistencias', 'errores',
            'outs_lanzados', 'carreras_permitidas', 'hits_permitidos',
            'base_por_bolas_permitidas', 'ponches_pitcheo',
        ]

    def __init__(self, *args, jugador=None, partido=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.jugador = jugador
        self.partido = partido

    def save(self, commit=True):
        juego = super().save(commit=False)
        juego.jugador = self.jugador
        juego.partido = self.partido
        juego.equipo = self.jugador.equipo
        if commit:
            juego.save()
        return juego


class PosicionForm(forms.ModelForm):
    class Meta:
        model = Posicion
        fields = ['equipo', 'fase', 'juegos', 'ganados', 'perdidos', 'empatados', 'carreras_favor', 'carreras_contra', 'puntos']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        etiqueta = lambda e: f"{e} — {e.campeonato.categoria.nombre} ({e.campeonato.temporada})"
        self.fields['equipo'].queryset = Equipo.objects.select_related(
            'campeonato', 'campeonato__categoria', 'club',
        ).order_by('campeonato__categoria__orden', 'club__nombre', 'escuadra')
        self.fields['equipo'].label_from_instance = etiqueta

    def save(self, commit=True):
        posicion = super().save(commit=False)
        posicion.campeonato = posicion.equipo.campeonato
        if commit:
            posicion.save()
        return posicion
