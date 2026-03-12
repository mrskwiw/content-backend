import os

os.chdir('operator-dashboard/src/components/wizard')

with open('TemplateSelectionPanel_new.tsx', 'w', encoding='utf-8') as f:
    f.write("import { useState, useEffect, memo } from 'react';\n")
    f.write("import { CheckCircle2, Circle, FileText, ArrowRight, AlertTriangle, Link2, Sparkles } from 'lucide-react';\n")
    f.write("import { PlatformSelector } from './PlatformSelector';\n")
    f.write("import { generatorApi, type TemplateDependencies } from '@/api/generator';\n")
    f.write("import { researchApi } from '@/api/research';\n\n")

print('Script created')
