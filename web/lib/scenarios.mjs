import { answerQuery } from './query.mjs';

const definitions = [
  {
    id: 'volume',
    title: '¿Dónde cambió la demanda?',
    question: 'Casos por mes',
    context: 'Compará los meses de ingreso para decidir qué período merece un análisis más profundo.',
    interpretation: 'Las barras muestran recepciones por mes. No representan cierres ocurridos ese mes; el mes del corte está incompleto.'
  },
  {
    id: 'open',
    title: '¿Qué cola revisar hoy?',
    question: 'Casos abiertos por equipo',
    context: 'La distribución de pendientes entre equipos orienta dónde comenzar el seguimiento diario.',
    interpretation: 'Es una instantánea actual. El backlog diario se calcula aparte con fechas de recepción y cierre.'
  },
  {
    id: 'sla',
    title: '¿Qué canal requiere revisión?',
    question: 'Cumplimiento SLA por canal',
    context: 'Compará el porcentaje de cumplimiento por canal antes de revisar casos concretos.',
    interpretation: 'El porcentaje usa casos resueltos como denominador y 48 horas corridas como regla sintética.'
  },
  {
    id: 'rejections',
    title: '¿Dónde revisar rechazos?',
    question: 'Rechazos por equipo en mayo 2023',
    context: 'Un cruce de estado, mes y equipo muestra dónde profundizar, sin atribuir causas.',
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
