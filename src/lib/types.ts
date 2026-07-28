export interface ImagenObra {
  archivo?: string;
  archivoAltaResolucion?: string;
  url?: string;
  urlAltaResolucion?: string;
  src: string;
  srcAltaResolucion?: string;
  alt: string;
  fuente: string;
  licencia: string;
  credito?: string;
  foco?: string;
}

export interface PestanaResumen {
  id: string;
  titulo: string;
  icono: string;
}

export interface ObraResumen {
  id: string;
  titulo: string;
  tituloOriginal?: string | null;
  autor: string;
  fecha: string;
  fechaOrden?: number | null;
  tipo: string;
  periodo: string;
  coleccion?: string | null;
  reconocimiento?: string | null;
  descripcion: string;
  localizacion?: string | null;
  ciudad?: string | null;
  urlLocalizacion?: string | null;
  urlMapa?: string | null;
  pais?: string | null;
  tecnicas?: string[];
  tieneAltaResolucion?: boolean;
  proporcion: [number, number];
  color: string;
  etiquetas: string[];
  imagen: ImagenObra;
  pestanas: PestanaResumen[];
}

export interface SeccionObra {
  id: string;
  titulo: string;
  icono: string;
  orden: number;
  contenido: string;
  archivo: string;
}

export interface ObraDetalle extends Omit<ObraResumen, 'pestanas'> {
  tecnicas?: string[];
  dimensiones?: string;
  cultura?: string;
  secciones: SeccionObra[];
}

export interface Catalogo {
  version: number;
  buildId: string;
  total: number;
  tipos: string[];
  periodos: string[];
  artistas: string[];
  colecciones: string[];
  obras: ObraResumen[];
}

export type OrdenCatalogo = 'azar' | 'antiguas' | 'recientes' | 'titulo';
export type Tema = 'auto' | 'claro' | 'oscuro';
