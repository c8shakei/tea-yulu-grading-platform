import * as echarts from 'echarts/core'
import { use } from 'echarts/core'
import { PieChart, LineChart, BarChart } from 'echarts/charts'
import {
  CanvasRenderer,
  SVGRenderer,
} from 'echarts/renderers'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  MarkLineComponent,
  MarkPointComponent,
} from 'echarts/components'

use([
  PieChart,
  LineChart,
  BarChart,
  CanvasRenderer,
  SVGRenderer,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  MarkLineComponent,
  MarkPointComponent,
])

export { echarts }
export default echarts
