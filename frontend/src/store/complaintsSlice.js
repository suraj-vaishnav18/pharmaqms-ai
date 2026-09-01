import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import * as apiClient from '../api/client'

export const fetchComplaints = createAsyncThunk('complaints/fetchAll', async () => {
  return await apiClient.listComplaints()
})

export const fetchComplaint = createAsyncThunk('complaints/fetchOne', async (id) => {
  return await apiClient.getComplaint(id)
})

export const addComplaint = createAsyncThunk('complaints/create', async (payload) => {
  return await apiClient.createComplaint(payload)
})

export const runPipeline = createAsyncThunk('complaints/runPipeline', async (id) => {
  return await apiClient.runAiPipeline(id)
})

const complaintsSlice = createSlice({
  name: 'complaints',
  initialState: {
    items: [],
    selected: null,
    status: 'idle', // idle | loading | succeeded | failed
    pipelineRunning: false,
    error: null,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchComplaints.pending, (state) => { state.status = 'loading' })
      .addCase(fetchComplaints.fulfilled, (state, action) => {
        state.status = 'succeeded'
        state.items = action.payload
      })
      .addCase(fetchComplaints.rejected, (state, action) => {
        state.status = 'failed'
        state.error = action.error.message
      })
      .addCase(fetchComplaint.fulfilled, (state, action) => {
        state.selected = action.payload
      })
      .addCase(addComplaint.fulfilled, (state, action) => {
        state.items.unshift(action.payload)
      })
      .addCase(runPipeline.pending, (state) => { state.pipelineRunning = true })
      .addCase(runPipeline.fulfilled, (state, action) => {
        state.pipelineRunning = false
        state.selected = action.payload
        const idx = state.items.findIndex(c => c.id === action.payload.id)
        if (idx !== -1) state.items[idx] = action.payload
      })
      .addCase(runPipeline.rejected, (state) => { state.pipelineRunning = false })
  },
})

export default complaintsSlice.reducer
