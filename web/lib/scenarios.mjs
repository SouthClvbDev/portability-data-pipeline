import { answerQuery } from './query.mjs';

const definitions = [
  {
    id: 'volume',
    title: '¿Cómo crece el volumen?',
    question: 'Casos por mes',
    context: 'Una mirada al ingreso de trámites a lo largo de la muestra.',
    interpretation: 'Las barras muestran recepciones por mes. No representan cierres ocurridos ese mes.'
  },
  {
    id: 'open',
    title: '¿Dónde están los pendientes?',
    question: 'Casos abiertos por equipo',
    context: 'El estado actual ayuda a localizar carga pendiente entre equipos.',
    interpretation: 'Es una instantánea. Para backlog histórico se necesitarían eventos de cambio de estado.'
  },
  {
    id: 'sla',
    title: '¿Cómo se distribuye el SLA?',
    question: 'Cumplimiento SLA por canal',
    context: 'Comparación de cumplimiento entre canales para casos ya resueltos.',
    interpretation: 'El porcentaje usa casos resueltos como denominador y 48 horas corridas como regla sintética.'
  },
  {
    id: 'rejections',
    title: '¿Quién gestionó los rechazos?',
    question: 'Rechazos por equipo en mayo',
    context: 'Un cruce concreto de estado, mes de recepción y equipo.',
    interpretation: 'El conteo no explica la causa del rechazo ni mide desempeño individual.'
  }
];

export function buildScenarios(records) {
  return definitions.map((definition) => {
    const { spec, result } = answerQuery(definition.question, records);
    if (!spec || !result.groups?.length) throw new Error(`Escenario sin datos: ${definition.id}`);
    return { ...definition, spec, total: result.cases, groups: result.groups };
  });
}
