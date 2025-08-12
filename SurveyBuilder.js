import React, { useState, useCallback } from 'react';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';

const FIELD_TYPES = [
  { type: 'text', label: 'Text Input', icon: '📝' },
  { type: 'textarea', label: 'Text Area', icon: '📄' },
  { type: 'number', label: 'Number', icon: '🔢' },
  { type: 'email', label: 'Email', icon: '📧' },
  { type: 'select', label: 'Dropdown', icon: '📋' },
  { type: 'radio', label: 'Radio Buttons', icon: '🔘' },
  { type: 'checkbox', label: 'Checkboxes', icon: '☑️' },
  { type: 'date', label: 'Date', icon: '📅' },
  { type: 'rating', label: 'Rating', icon: '⭐' },
];

const SurveyBuilder = ({ survey, onSurveyChange }) => {
  const [selectedField, setSelectedField] = useState(null);
  const [fields, setFields] = useState(survey?.fields || []);

  const handleDragEnd = useCallback((result) => {
    if (!result.destination) return;

    const { source, destination } = result;

    if (source.droppableId === 'field-types' && destination.droppableId === 'survey-fields') {
      // Adding new field from palette
      const fieldType = FIELD_TYPES[source.index];
      const newField = {
        id: `field_${Date.now()}`,
        type: fieldType.type,
        label: `New ${fieldType.label}`,
        required: false,
        options: fieldType.type === 'select' || fieldType.type === 'radio' || fieldType.type === 'checkbox' 
          ? [{ value: 'option1', label: 'Option 1' }] 
          : undefined,
        validation: {},
      };

      const newFields = [...fields];
      newFields.splice(destination.index, 0, newField);
      setFields(newFields);
      onSurveyChange({ ...survey, fields: newFields });
    } else if (source.droppableId === 'survey-fields' && destination.droppableId === 'survey-fields') {
      // Reordering existing fields
      const newFields = Array.from(fields);
      const [reorderedField] = newFields.splice(source.index, 1);
      newFields.splice(destination.index, 0, reorderedField);
      setFields(newFields);
      onSurveyChange({ ...survey, fields: newFields });
    }
  }, [fields, survey, onSurveyChange]);

  const updateField = useCallback((fieldId, updates) => {
    const newFields = fields.map(field => 
      field.id === fieldId ? { ...field, ...updates } : field
    );
    setFields(newFields);
    onSurveyChange({ ...survey, fields: newFields });
  }, [fields, survey, onSurveyChange]);

  const deleteField = useCallback((fieldId) => {
    const newFields = fields.filter(field => field.id !== fieldId);
    setFields(newFields);
    onSurveyChange({ ...survey, fields: newFields });
    if (selectedField?.id === fieldId) {
      setSelectedField(null);
    }
  }, [fields, survey, onSurveyChange, selectedField]);

  const addOption = useCallback((fieldId) => {
    const field = fields.find(f => f.id === fieldId);
    if (field && field.options) {
      const newOption = {
        value: `option${field.options.length + 1}`,
        label: `Option ${field.options.length + 1}`
      };
      updateField(fieldId, {
        options: [...field.options, newOption]
      });
    }
  }, [fields, updateField]);

  const updateOption = useCallback((fieldId, optionIndex, updates) => {
    const field = fields.find(f => f.id === fieldId);
    if (field && field.options) {
      const newOptions = field.options.map((option, index) =>
        index === optionIndex ? { ...option, ...updates } : option
      );
      updateField(fieldId, { options: newOptions });
    }
  }, [fields, updateField]);

  const removeOption = useCallback((fieldId, optionIndex) => {
    const field = fields.find(f => f.id === fieldId);
    if (field && field.options && field.options.length > 1) {
      const newOptions = field.options.filter((_, index) => index !== optionIndex);
      updateField(fieldId, { options: newOptions });
    }
  }, [fields, updateField]);

  return (
    <DragDropContext onDragEnd={handleDragEnd}>
      <div className="flex h-full bg-gray-50">
        {/* Field Types Palette */}
        <div className="w-64 bg-white border-r border-gray-200 p-4">
          <h3 className="text-lg font-semibold mb-4">Field Types</h3>
          <Droppable droppableId="field-types" isDropDisabled={true}>
            {(provided) => (
              <div {...provided.droppableProps} ref={provided.innerRef}>
                {FIELD_TYPES.map((fieldType, index) => (
                  <Draggable
                    key={fieldType.type}
                    draggableId={fieldType.type}
                    index={index}
                  >
                    {(provided, snapshot) => (
                      <div
                        ref={provided.innerRef}
                        {...provided.draggableProps}
                        {...provided.dragHandleProps}
                        className={`p-3 mb-2 border border-gray-200 rounded-lg cursor-move hover:bg-gray-50 ${
                          snapshot.isDragging ? 'bg-blue-50 border-blue-300' : ''
                        }`}
                      >
                        <div className="flex items-center">
                          <span className="text-xl mr-2">{fieldType.icon}</span>
                          <span className="text-sm font-medium">{fieldType.label}</span>
                        </div>
                      </div>
                    )}
                  </Draggable>
                ))}
                {provided.placeholder}
              </div>
            )}
          </Droppable>
        </div>

        {/* Survey Builder Area */}
        <div className="flex-1 p-6">
          <div className="mb-6">
            <input
              type="text"
              placeholder="Survey Title"
              value={survey?.title || ''}
              onChange={(e) => onSurveyChange({ ...survey, title: e.target.value })}
              className="text-2xl font-bold w-full border-none outline-none bg-transparent"
            />
            <textarea
              placeholder="Survey Description"
              value={survey?.description || ''}
              onChange={(e) => onSurveyChange({ ...survey, description: e.target.value })}
              className="w-full mt-2 p-2 border border-gray-200 rounded-lg resize-none"
              rows="2"
            />
          </div>

          <Droppable droppableId="survey-fields">
            {(provided) => (
              <div {...provided.droppableProps} ref={provided.innerRef} className="min-h-96">
                {fields.length === 0 && (
                  <div className="text-center py-12 text-gray-500">
                    <p className="text-lg">Drag field types here to build your survey</p>
                  </div>
                )}
                {fields.map((field, index) => (
                  <Draggable key={field.id} draggableId={field.id} index={index}>
                    {(provided, snapshot) => (
                      <div
                        ref={provided.innerRef}
                        {...provided.draggableProps}
                        className={`mb-4 p-4 bg-white border border-gray-200 rounded-lg ${
                          snapshot.isDragging ? 'shadow-lg' : ''
                        } ${selectedField?.id === field.id ? 'border-blue-500' : ''}`}
                        onClick={() => setSelectedField(field)}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div {...provided.dragHandleProps} className="cursor-move p-1">
                            <span className="text-gray-400">⋮⋮</span>
                          </div>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              deleteField(field.id);
                            }}
                            className="text-red-500 hover:text-red-700"
                          >
                            ✕
                          </button>
                        </div>
                        <FieldPreview field={field} />
                      </div>
                    )}
                  </Draggable>
                ))}
                {provided.placeholder}
              </div>
            )}
          </Droppable>
        </div>

        {/* Field Properties Panel */}
        {selectedField && (
          <div className="w-80 bg-white border-l border-gray-200 p-4">
            <h3 className="text-lg font-semibold mb-4">Field Properties</h3>
            <FieldProperties
              field={selectedField}
              onUpdate={(updates) => updateField(selectedField.id, updates)}
              onAddOption={() => addOption(selectedField.id)}
              onUpdateOption={updateOption}
              onRemoveOption={removeOption}
            />
          </div>
        )}
      </div>
    </DragDropContext>
  );
};

const FieldPreview = ({ field }) => {
  const renderField = () => {
    switch (field.type) {
      case 'text':
        return <input type="text" placeholder="Text input" className="w-full p-2 border border-gray-300 rounded" disabled />;
      case 'textarea':
        return <textarea placeholder="Text area" className="w-full p-2 border border-gray-300 rounded" rows="3" disabled />;
      case 'number':
        return <input type="number" placeholder="Number input" className="w-full p-2 border border-gray-300 rounded" disabled />;
      case 'email':
        return <input type="email" placeholder="Email input" className="w-full p-2 border border-gray-300 rounded" disabled />;
      case 'date':
        return <input type="date" className="w-full p-2 border border-gray-300 rounded" disabled />;
      case 'select':
        return (
          <select className="w-full p-2 border border-gray-300 rounded" disabled>
            {field.options?.map((option, index) => (
              <option key={index} value={option.value}>{option.label}</option>
            ))}
          </select>
        );
      case 'radio':
        return (
          <div>
            {field.options?.map((option, index) => (
              <label key={index} className="flex items-center mb-2">
                <input type="radio" name={field.id} value={option.value} className="mr-2" disabled />
                {option.label}
              </label>
            ))}
          </div>
        );
      case 'checkbox':
        return (
          <div>
            {field.options?.map((option, index) => (
              <label key={index} className="flex items-center mb-2">
                <input type="checkbox" value={option.value} className="mr-2" disabled />
                {option.label}
              </label>
            ))}
          </div>
        );
      case 'rating':
        return (
          <div className="flex">
            {[1, 2, 3, 4, 5].map((star) => (
              <span key={star} className="text-2xl text-gray-300 cursor-pointer">⭐</span>
            ))}
          </div>
        );
      default:
        return <div className="text-gray-500">Unknown field type</div>;
    }
  };

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">
        {field.label}
        {field.required && <span className="text-red-500 ml-1">*</span>}
      </label>
      {renderField()}
    </div>
  );
};

const FieldProperties = ({ field, onUpdate, onAddOption, onUpdateOption, onRemoveOption }) => {
  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Label</label>
        <input
          type="text"
          value={field.label}
          onChange={(e) => onUpdate({ label: e.target.value })}
          className="w-full p-2 border border-gray-300 rounded"
        />
      </div>

      <div>
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={field.required}
            onChange={(e) => onUpdate({ required: e.target.checked })}
            className="mr-2"
          />
          Required field
        </label>
      </div>

      {(field.type === 'select' || field.type === 'radio' || field.type === 'checkbox') && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Options</label>
          {field.options?.map((option, index) => (
            <div key={index} className="flex items-center mb-2">
              <input
                type="text"
                value={option.label}
                onChange={(e) => onUpdateOption(field.id, index, { label: e.target.value, value: e.target.value.toLowerCase().replace(/\s+/g, '_') })}
                className="flex-1 p-2 border border-gray-300 rounded mr-2"
              />
              {field.options.length > 1 && (
                <button
                  onClick={() => onRemoveOption(field.id, index)}
                  className="text-red-500 hover:text-red-700"
                >
                  ✕
                </button>
              )}
            </div>
          ))}
          <button
            onClick={onAddOption}
            className="text-blue-500 hover:text-blue-700 text-sm"
          >
            + Add Option
          </button>
        </div>
      )}

      {field.type === 'text' && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Max Length</label>
          <input
            type="number"
            value={field.validation?.maxLength || ''}
            onChange={(e) => onUpdate({ 
              validation: { 
                ...field.validation, 
                maxLength: e.target.value ? parseInt(e.target.value) : undefined 
              } 
            })}
            className="w-full p-2 border border-gray-300 rounded"
          />
        </div>
      )}

      {field.type === 'number' && (
        <>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Min Value</label>
            <input
              type="number"
              value={field.validation?.min || ''}
              onChange={(e) => onUpdate({ 
                validation: { 
                  ...field.validation, 
                  min: e.target.value ? parseFloat(e.target.value) : undefined 
                } 
              })}
              className="w-full p-2 border border-gray-300 rounded"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Max Value</label>
            <input
              type="number"
              value={field.validation?.max || ''}
              onChange={(e) => onUpdate({ 
                validation: { 
                  ...field.validation, 
                  max: e.target.value ? parseFloat(e.target.value) : undefined 
                } 
              })}
              className="w-full p-2 border border-gray-300 rounded"
            />
          </div>
        </>
      )}
    </div>
  );
};

export default SurveyBuilder;

